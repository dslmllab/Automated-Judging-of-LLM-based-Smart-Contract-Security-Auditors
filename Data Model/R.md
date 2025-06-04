Reviewer1:

Thank you for positive feedback and giving the strong accept. We have additional experimental details in GitHub link along with demo video. that covers the evaluation of smart contract auditing tools, and evaluation of agenticRAG in identifying complex vulnerability patterns.

Reviewer2:

Figure 3, illustrates the workflow of smartJudge, which is initiated with the results of LLM powered auditors details which is being evaluated/judged by the smartJudge. Steps 1 and Step 9 are the interactions between LLM powered auditor results and smartJudge.

The detailed analysis report from the smartJudge provides the insights LLM auditing tool.

We have built agenticRAG, which powers traditional RAG with automated Agents. This enables us to leverage benefits of RAG and build efficient retrievable information from local on device data.

We will improve the readability of Figures and Tables in our final version.

We strongly believe our approach can be used to evaluate any automated smart contract auditing tools. The 8-page limit for the paper made us leverage the space for technical details of proposed approach. And we used GitHub space for sharing experimental demos and results.


Reviewer3:

We would like to highlight our disappoint with reviewer3 comments on lacking convincing arguments as we have spent 8 pages content to explain the technical details and motivation of proposed approach.

Our proposed approach smartJudge purpose is to evaluate Smart Contract Auditing tools, we have built a pipeline with agenticRAGs to make the smartJudge resourceful with abundant knowledge on smart contracts technical expertise, Vulnerabilities.

With the trending expertise of LLMs to trick the evaluation strategies and scoreboards by learning predefined Benchmarks we have designed an Evaluation strategy which will be difficult for the LLMs to learn and trick the evaluation methodologies to gain high scores.

That would be the reason for not having a predefined static Benchmark dataset but only the Benchmark Metrics to quantify the performance of the LLM based auditors.


We have already provided the Github link in the paper (section4.b) with additional experimental evidence, a README.md to replicate, reuse the proposed approach for any new auditor. And also, a demo on how to leverage the proposed approach and evaluate the automated auditors.

As LLM Based auditors are the trending new Smart Contract auditors, we have focused on evaluating them and creating a standardized benchmark. We believe it could be reused for evaluating any bug detection tool if it is on Solidity code.

As suggested, we can cutdown Table in related work section and include few more results, a copy of them is on Github Results folder.


https://github.com/aiexpert7/Automated-Judging-of-LLM-based-Smart-Contract-Security-Auditors



