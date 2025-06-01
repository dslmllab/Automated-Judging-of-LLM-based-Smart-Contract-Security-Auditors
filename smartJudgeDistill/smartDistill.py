from openai import OpenAI
from typing import List, Dict
import json

class ContractDistiller:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = """You are a smart contract auditor, identify and explain severe vulnerabilities in the provided smart contract. Provide each identified vulnerability with intermediate reasoning and its associated function. Make your reasoning comprehensive and detailed."""

    def generate_training_data(self, contracts: List[Dict[str, str]],
                               large_model: str = "gpt-4") -> List[Dict]:
        training_data = []

        for contract in contracts:
            response = self.client.chat.completions.create(
                model=large_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Audit:\n{contract['code']}"}
                ],
                store=True,
                metadata={"type": "audit", "platform": contract.get("platform", "ethereum")}
            )

            training_data.append({
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Audit:\n{contract['code']}"},
                    {"role": "assistant", "content": response.choices[0].message.content}
                ]
            })

        return training_data

    def fine_tune(self, training_data: List[Dict], model: str = "gpt-3.5-turbo"):
        training_file = "training.jsonl"
        with open(training_file, 'w') as f:
            for item in training_data:
                f.write(json.dumps(item) + '\n')

        file = self.client.files.create(file=open(training_file, 'rb'), purpose='fine-tune')
        job = self.client.fine_tuning.jobs.create(
            training_file=file.id,
            model=model
        )
        return job.id

# Usage
contracts = [
    {
        "name": "Reentrancy",
        "platform": "ethereum",
        "code": """
        contract Token {
            mapping(address => uint) balances;
            function withdraw() public {
                uint amount = balances[msg.sender];
                (bool success, ) = msg.sender.call{value: amount}("");
                require(success);
                balances[msg.sender] = 0;
            }
        }
        """
    }
]

distiller = ContractDistiller(api_key="sk-proj*")
training_data = distiller.generate_training_data(contracts)
job_id = distiller.fine_tune(training_data)
print(f"Fine-tuning job started: {job_id}")