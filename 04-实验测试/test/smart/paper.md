1\]\\orgnameCollege of Computer and Information Science, Southwest University, \\orgaddress\\cityChongqing, \\countryChina 2\]\\orgnameCollege of Science and Technology, Nihon University, \\orgaddress\\cityChiba, \\countryJapan 3\]\\orgnameShenzhen International Graduate School, Tsinghua University, \\orgaddress\\cityShenzhen, \\countryChina 4\]\\orgnameWaseda Institute for Advanced Study, Waseda University, \\orgaddress\\cityTokyo, \\countryJapan

###### Abstract

The widespread adoption of the “Games as a Service” model necessitates frequent content updates, placing immense pressure on quality assurance. In response, automated game testing has been viewed as a promising solution to cope with this demanding release cadence. However, existing automated testing approaches typically create a dichotomy: code-centric methods focus on structural coverage without understanding gameplay context, while player-centric agents validate high-level intent but often fail to cover specific underlying code changes. To bridge this gap, we propose SMART (Structural Mapping for Augmented Reinforcement Testing), a novel framework that synergizes structural verification and functional validation for game update testing. SMART leverages Large Language Models (LLMs) to interpret Abstract Syntax Tree (AST) differences and extract functional intent, constructing a context-aware hybrid reward mechanism. This mechanism guides Reinforcement Learning agents to sequentially fulfill gameplay goals while adaptively exploring modified code branches. We evaluate SMART on two environments, Overcooked and Minecraft. The results demonstrate that SMART significantly outperforms state-of-the-art baselines; it achieves over 94% branch coverage of modified code, nearly double that of traditional RL methods, while maintaining a 98% task completion rate, effectively balancing structural comprehensiveness with functional correctness.

###### keywords:

Game Testing, Game Updates, Large Language Model, Reinforcement Learning

## 1 Introduction

The global video game industry has evolved into an economic and cultural powerhouse, with market revenues reaching hundreds of billions of dollars annually \[[1](https://arxiv.org/html/2512.12706v1#bib.bib1)\]. In such a fiercely competitive landscape, the software quality assurance (QA) is not merely a technical step but a cornerstone of commercial success. Rigorous game testing is essential to ensure functionality, stability, and a polished user experience, as post-launch bugs can severely damage player trust, brand reputation, and revenue streams \[[2](https://arxiv.org/html/2512.12706v1#bib.bib2)\].

This landscape is further complicated by the industry’s widespread adoption of the “Games as a Service” (GaaS) model. Unlike traditional single-purchase titles, GaaS products are continuously evolving entities, sustained by a frequent cadence of updates and content patches (e.g., new game quests and materials) designed to maintain player engagement \[[3](https://arxiv.org/html/2512.12706v1#bib.bib3)\]. While these updates are crucial for player retention and monetization, each patch—whether introducing new features or modifying existing ones—carries the inherent risk of introducing unforeseen defects into a stable codebase. This relentless development cycle places immense pressure on testing teams, demanding automated testing methodologies that are highly efficient and responsive to rapid iteration.

In response to these demands, automated game testing has emerged as a critical area of research. These studies can be bifurcated into two distinct paradigms. The first paradigm, rooted in conventional software engineering, adopts a code-centric perspective. Utilizing white-box or grey-box techniques, it prioritizes the structural testing of the program through methods such as unit testing and static analysis. The principal metric in this line of work is code coverage, aiming to ensure that every line of logic within the codebase is executed. In contrast, the second paradigm is player-centric, employing beta testing to focus on the functional correctness and behavioral validity of the game. Studies in this tradition validate high-level gameplay scenarios—such as whether a quest can be successfully completed. The overarching goal is to ensure that the game functions as intended from an end-user perspective.

However, we argue that this dichotomous division is increasingly insufficient for the modern "Game as a Service" (GaaS) model, where games are subject to content updates. A typical game content update inherently constitutes a hybrid of functional and structural changes: it may introduce new quests (macro-level functional gameplay intent) while also incorporating new elements (such as new items, new interaction methods, etc.) (micro-level structural changes). As such, single-dimensional testing approaches are inadequate. For example, a test suite focused solely on code coverage may confirm the execution of a modified numerical parameter but cannot determine whether the adjustment yields the desired gameplay intent. Conversely, functional tests that only assess new quest flows may entirely fail to cover all the new code.

To this end, this paper proposes SMART(Structural Mapping for Augmented Reinforcement Testing), an incremental hybrid testing framework designed to systematically integrate both structural verification and functional validation. Specifically, we employ Large Language Models (LLMs) to interpret code updates, decomposing them into sequential functional subgoals aligned with specific structural anchors. These inputs are integrated into an adaptive hybrid reward mechanism that motivates the Reinforcement Learning (RL) agent to pursue dual objectives: validating gameplay intent through goal completion, while exploring edge-case interactions to maximize the coverage of modified code branches.

The contributions of this paper are as follows:

-   •
    
    We propose SMART, a novel testing framework that systematically combines low-level code modifications with high-level functional validation. Specifically, SMART utilizes a hybrid reward mechanism–integrating LLM—extracted semantic signals with AST-based structural signals—to guide agents in validating gameplay logic while actively exploring edge-case interactions within the modified code.
    
-   •
    
    We introduce a context-aware mapping methodology to enable precise hybrid guidance. The functional intent of an update is decomposed into ordered semantic subgoals, while low-level code modifications are represented as structural anchors. A dynamic mapping between the two ensures that the agent is rewarded only for covering structural changes relevant to the current gameplay stage, thereby preventing inefficient exploration of irrelevant or unreachable code paths.
    
-   •
    
    We conduct experiments on two games, Overcooked and Minecraft, to evaluate the effectiveness of SMART.
    

The rest of this paper is structured as follows. Section [2](https://arxiv.org/html/2512.12706v1#S2 "2 Background ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning") establishes the technical background. Section [3](https://arxiv.org/html/2512.12706v1#S3 "3 Proposal ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning") elaborates on the design and implementation of our SMART framework. Section [4](https://arxiv.org/html/2512.12706v1#S4 "4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning") presents our experimental setup, results, and discussion. Section [5](https://arxiv.org/html/2512.12706v1#S5 "5 Related Work ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning") reviews prior work on automated game testing and the application of LLMs. Finally, Section [6](https://arxiv.org/html/2512.12706v1#S6 "6 Conclusion and Future Work ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning") concludes the paper and outlines future work.

## 2 Background

### 2.1 Abstract Syntax Tree (AST)

An Abstract Syntax Tree (AST) is a tree-based representation of the syntactic structure of source code \[[4](https://arxiv.org/html/2512.12706v1#bib.bib4)\]. From the perspective of graph theory, an AST can be regarded as a special kind of Directed Acyclic Graph (DAG), where each node represents a syntactic construct in the source code, and edges represent the hierarchical and logical relationships between these constructs.

Formally, a family of ASTs, denoted 𝒜\[𝒳\]\\mathcal{A}\[\\mathcal{X}\], can be defined inductively. Let SS be a finite set of sorts (for example, “expression”, “statement”, etc.), and let 𝒪\\mathcal{O} be a set of operators (such as ‘+’, ‘if’), each associated with an arity describing the types of its arguments. Given a family of variable sets 𝒳\\mathcal{X} indexed by sorts, the family of ASTs 𝒜\[𝒳\]\\mathcal{A}\[\\mathcal{X}\] is the smallest collection satisfying:

-   •
    
    Variables are ASTs: If x∈𝒳sx\\in\\mathcal{X}\_{s}, then x∈𝒜\[𝒳\]sx\\in\\mathcal{A}\[\\mathcal{X}\]\_{s}.
    
-   •
    
    Operators combine ASTs: If an operator oo has arity (s1,…,sn)s(s\_{1},\\dots,s\_{n})s, and for all 1≤i≤n1\\leq i\\leq n, ai∈𝒜\[𝒳\]sia\_{i}\\in\\mathcal{A}\[\\mathcal{X}\]\_{s\_{i}}, then o(a1,…,an)∈𝒜\[𝒳\]so(a\_{1},\\dots,a\_{n})\\in\\mathcal{A}\[\\mathcal{X}\]\_{s}.
    

The “abstract” in AST distinguishes it from the Concrete Syntax Tree (CST, or parse tree) that is typically generated by the parser in the early stages of compilation. While a concrete syntax tree faithfully represents every syntactic detail from the source text, the AST omits non-essential elements for structural understanding, such as parentheses used for grouping, semicolons terminating statements, and formatting artifacts like indentation or newlines. Instead, the AST is designed to capture the structural and semantic content of the code, rather than its surface textual representation.

Within the AST, different language constructs are clearly expressed through their hierarchical relationships. For example, an if-else statement is usually represented by an ‘If’ node, which has at least two children: the first child denotes the condition expression, and the second child represents the ‘then’ code block. If there is an ‘else’ or ‘else if’ branch, it appears as a third child (the orelse node). Another example is the loop statement: a ‘for’ loop is typically represented by a ‘For’ node, which has multiple children corresponding to the initialization variable, the loop termination condition, the update operation after each iteration, and the loop body itself. Thanks to this hierarchical tree structure, the AST is typically a direct product of the syntactic analysis phase and serves as a crucial intermediate representation (IR) throughout many stages of software compilation and analysis \[[5](https://arxiv.org/html/2512.12706v1#bib.bib5), [6](https://arxiv.org/html/2512.12706v1#bib.bib6)\].

### 2.2 Reinforcement Learning

Reinforcement Learning (RL) is an important branch of machine learning that studies how an agent can learn to make decisions through interactions with an environment, with the objective of maximizing the cumulative reward it receives \[[7](https://arxiv.org/html/2512.12706v1#bib.bib7)\]. This learning paradigm is particularly well-suited to solving complex problems that require sequential decision-making, such as video games \[[8](https://arxiv.org/html/2512.12706v1#bib.bib8)\].

The RL problem is typically modeled as a Markov Decision Process (MDP), which is formally defined by a five-tuple (S,A,P,R,γ)(S,A,P,R,\\gamma). Here, SS denotes the set of all possible environment states, while AA represents the set of actions that the agent can perform. The transition probability function P(s′|s,a)P(s^{\\prime}|s,a) defines the probability of transitioning to state s′s^{\\prime} when the agent takes action aa in state ss. The reward function R(s,a,s′)R(s,a,s^{\\prime}) specifies the immediate reward signal the agent receives after performing action aa in state ss and transitioning to s′s^{\\prime}. The discount factor γ∈\[0,1\]\\gamma\\in\[0,1\] balances the importance of short-term and long-term rewards. The agent’s behavior is determined by its policy π(a|s)\\pi(a|s), which gives the probability of selecting action aa when in state ss. The goal of RL algorithms is to learn an optimal policy π∗\\pi^{\*} that maximizes the expected cumulative discounted reward—also known as return—from any initial state.

Among the many RL algorithms, Proximal Policy Optimization (PPO) has become one of the most popular and effective approaches due to its excellent sample efficiency and training stability \[[9](https://arxiv.org/html/2512.12706v1#bib.bib9)\]. PPO belongs to the family of policy gradient methods and optimizes a “clipped” surrogate objective to restrict the step size of each policy update. The core objective function is defined as follows:

|  | LCLIP(θ)=𝔼^t[min⁡(rt(θ)A^t,clip(rt(θ),1−ϵ,1+ϵ)A^t)]L^{CLIP}(\theta)=\hat{\mathbb{E}}_{t}\left[\min\left(r_{t}(\theta)\hat{A}_{t},\mathrm{clip}(r_{t}(\theta),1-\epsilon,1+\epsilon)\hat{A}_{t}\right)\right] |  | (1) |
|-----|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----|-----|

In this formulation, 𝔼^t\\hat{\\mathbb{E}}\_{t} denotes the empirical average over timesteps tt. The term rt(θ)\=πθ(at|st)πθold(at|st)r\_{t}(\\theta)=\\frac{\\pi\_{\\theta}(a\_{t}|s\_{t})}{\\pi\_{\\theta\_{\\text{old}}}(a\_{t}|s\_{t})} represents the probability ratio of the new and old policies for a given action, where πθ\\pi\_{\\theta} is the current policy being optimized and πθold\\pi\_{\\theta\_{\\text{old}}} is the policy from the previous iteration. The term A^t\\hat{A}\_{t} denotes an estimate of the advantage function at time tt, which measures how much better (or worse) taking action ata\_{t} in state sts\_{t} is compared to the average. The function clip(x,min,max)\\mathrm{clip}(x,\\min,\\max) restricts its input xx to the interval \[min,max\]\[\\min,\\max\], and ϵ\\epsilon is a small hyperparameter (typically 0.2) defining the clipping range. By constraining the probability ratio rt(θ)r\_{t}(\\theta) within a certain range, this objective ensures that policy updates do not deviate too far from the previous policy, thereby improving the stability of the learning process.

## 3 Proposal

### 3.1 Overview

![Refer to caption](https://arxiv.org/html/figures/overview_v7.png)

Figure 1: Architectural overview of the SMART framework, where green boxes represent the core processing stages of the framework, blue boxes denote the intermediate data artifacts.

As illustrated in Figure [1](https://arxiv.org/html/2512.12706v1#S3.F1 "Figure 1 ‣ 3.1 Overview ‣ 3 Proposal ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning"), SMART synergizes the structural code changes and functional gameplay intent through a systematic five-stage pipeline. The pipeline consists of five stages: (i) AST Difference Parsing, which identifies all modified lines and branches between game versions by comparing their ASTs; (ii) Semantic Subgoal Generation, which decomposes the new quests into an ordered sequence of natural language subgoals using LLMs; (iii) Semantic Reward Generation, which converts the natural language subgoal sequence into a corresponding sequence of machine-executable RL reward functions; (iv) Structural Anchor Mapping, which establishes a context-aware link between each low-level code and branch change and the specific high-level subgoal(s) it is related to; and (v) Adaptive Hybrid Reward Function, which conducts the testing process by guiding an RL agent with a hybrid reward that combines sequential subgoal completion with the discovery of novel code coverage. This hybrid reward function effectively separates concerns: the semantic reward ensures the agent learns what to do (functional correctness), while the adaptive structural reward ensures it explores how else it can be done (structural comprehensiveness).

In the remainder of this section, we first provide a motivating example, followed by detailed technical descriptions of each component.

### 3.2 Motivating Example

To more clearly and intuitively illustrate our approach, we present a motivating example from an Overcooked-style cooking game. Suppose a game update adds items such as dough and an oven, which then creates several quests. One of these quests is called "Onion Pizza". This quest requires the player to prepare a onion pizza by assembling multiple ingredients in a specific order and baking the assembled pizza in an oven.

Concretely, the updated quest logic requires the player to (i) obtain a dough base and place it on a counter, (ii) fetch a tomato and chop it on a cutting board, (iii) add chopped tomato and cheese onto the dough to form a raw tomato pizza, (iv) bake the raw pizza in the oven until it becomes a finished pizza, (v) place the baked pizza on a plate, and then (vi) fetch an onion, chop it, and sprinkle the chopped onion onto the plated pizza before finally delivering it at the delivery station. This process forms a multi-step cooking sequence that naturally decomposes into a set of intermediate gameplay subgoals.

At the same time, the Pizza Onion quest update introduces several low-level modifications in the codebase. These include the definition of new item states for tomatoes and onions (e.g., whole vs. chopped), the handling of dough, tomato, and cheese combinations on counters, the baking logic inside the oven that transforms a raw pizza into a finished pizza, and the post-baking logic that allows a plated pizza to accept an additional onion topping. Additional code is also added around the delivery station to validate that only correctly assembled and decorated onion pizzas are accepted as valid quest completions.

### 3.3 AST Difference Parser

After a game update, the AST Difference Parser first compares the source code of the new and old versions to identify the locations and content of code changes. Specifically, it constructs ASTs for both the pre-update and post-update versions of the code. A tree-differencing algorithm then compares these two ASTs to identify added, modified, and deleted nodes, ignoring purely stylistic changes like whitespace.

The raw output of this process is a detailed list of AST node differences. To make these changes actionable for testing, this stage processes the raw diffs to populate two distinct sets of testable sets, (CLC\_{L}, CBC\_{B}), which we term structural anchors:

-   •
    
    Modified Lines (CLC\_{L}): This is the set of individual lines of code that have been added or substantively modified. Each entry l∈CLl\\in C\_{L} is uniquely identified by its location (e.g., file path and line number) and represents a discrete statement that must be executed to be considered covered.
    
-   •
    
    Modified Branches (CBC\_{B}): This is the set of newly introduced or altered logical branches within control-flow statements (e.g., ‘if’, ‘switch’, ‘while’). A change to a control-flow node in the AST—such as modifying the condition of an ‘if’ statement—results in its corresponding logical paths being added to this set. For instance, a modified ‘if-else’ statement contributes two branches to CBC\_{B}: one for the ‘true’ condition and one for the ‘false’ condition. Each branch b∈CBb\\in C\_{B} is identified by the location of its control statement and the specific condition that activates it.
    

### 3.4 Stage 2: Subgoal Generation

Given the code updating the corresponding to one new game quest, the LLM-powered Subgoal Generator is tasked with analyzing the raw code changes associated with a single, complex game quest and decomposing it into a logically ordered sequence of subgoals. By analyzing function calls, data dependencies (e.g., a function requiring ‘chopped\_tomato’ as input), and quest logic extracted from the AST Diffs, the LLM infers the necessary intermediate steps. For instance, after parsing the code updates related to the "Onion Pizza" task, the Subgoal generator sequentially identifies a series of verifiable natural language sub-goals from the overall task, such as "get and place the dough", "process the tomatoes and assemble the raw pizza", and "bake the pizza and add chopped onions", forming an ordered sequence of sub-goals (see Listing [4](https://arxiv.org/html/2512.12706v1#LST4 "Listing 4 ‣ Appendix ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning")).

The final output of this stage is a semantically meaningful and ordered sequence of subgoals, denoted as S\=(sg1,sg2,…,sgn)S=(sg\_{1},sg\_{2},\\dots,sg\_{n}). Each element sgj∈Ssg\_{j}\\in S is a natural language string describing a distinct, verifiable step of the overall task. For the pizza quest example, this sequence would be: (i) sg1sg\_{1}: "Obtain and chop a tomato"; (ii) sg2sg\_{2}: "Process the chopped tomato into sauce using a mixer"; (iii) sg3sg\_{3}: "Assemble the pizza on a base with sauce and cheese"; and (iv) sg4sg\_{4}: "Bake the assembled pizza in the oven."

### 3.5 Stage 3: Semantic Reward Generation

To make the abstract subgoals from Stage 2 actionable, the LLM-driven semantic reward generator translates each step’s objective into a formally defined, executable reward rule. This component is provided with the subgoal sequence SS and the game’s environment observation schema, a manifest detailing all observable state variables.

For each subgoal sgjsg\_{j} in the sequence SS, the LLM is prompted to generate a specific reward rule. This rule defines a success condition for that particular step using only the variables available in the observation schema. This process transforms the high-level natural language plan into a machine-verifiable format. For instance, for the sub-goal "baking pizza", the generator creates one reward for putting the raw pizza into the oven; one reward for each observable improvement in baking progress; and one final reward triggered when the pizza transitions from a raw state to a finished state, then outputs them in JSON format.(see Listing [5](https://arxiv.org/html/2512.12706v1#LST5 "Listing 5 ‣ Appendix ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning"))

Based on the subgoal sequence S\=(sg1,sg2,…,sgn)S=(sg\_{1},sg\_{2},\\dots,sg\_{n}) from Stage 2, this stage generates a corresponding ordered sequence of reward functions, denoted as R\=(r1,r2,…,rn)R=(r\_{1},r\_{2},\\dots,r\_{n}). Each function rj:State→ℝr\_{j}:\\text{State}\\to\\mathbb{R} is a binary predicate corresponding to subgoal sgjsg\_{j}. It returns a positive reward if and only if the success conditions for sgjsg\_{j} are met in the current game state, and zero otherwise. This sequence RR provides the series of checkpoints that the agent must achieve in the correct order, forming the backbone of the guidance mechanism detailed in Stage 5.

### 3.6 Stage 4: Structural Anchor Mapping

This stage forges the critical link between the high-level subgoals and the specific low-level code that needs to be triggered. In a multi-step quest, the code relevant to the player changes as they progress. For instance, after a tomato is chopped (Subgoal 1), the code related to the interaction between a whole tomato and a cutting board will never again be triggered during normal gameplay. Therefore, a context-aware mapping—i.e., determining which code segments should be tested at which subgoal stage—is essential.

###### Definition 1 (Structural Anchor Mapping).

Let S\=S=  
{sg1,sg2,…,sgn}\\{sg\_{1},sg\_{2},\\dots,sg\_{n}\\} be the ordered set of subgoals from Stage 2. Let CLC\_{L} and CBC\_{B} be the sets of modified lines and branches, respectively, identified by the AST Difference Parser in Stage 1. We define the comprehensive set of all structural anchors as C\=CL∪CBC=C\_{L}\\cup C\_{B}. The goal of this stage is to construct a mapping function M:C→𝒫(S)M:C\\to\\mathcal{P}(S), where 𝒫(S)\\mathcal{P}(S) is the power set of SS. This function assigns each structural anchor ci∈Cc\_{i}\\in C to a non-empty subset of subgoals M(ci)⊆SM(c\_{i})\\subseteq S during which it is considered relevant and testable. The mapping must be comprehensive, ensuring that for every anchor cic\_{i}, its assigned set of subgoals M(ci)M(c\_{i}) is not empty. A single anchor can be mapped to multiple subgoals (i.e., |M(ci)|≥1|M(c\_{i})|\\geq 1).

To construct this mapping, we employ a two-phase hybrid approach. First, we perform a static analysis to establish a coarse-grained reachability relationship. For each subgoal, we identify its primary entry point in the code. From these entry points, we trace backwards through the call graph and data dependencies to identify a candidate set of all potentially reachable structural anchors from CC. This initial pass provides a conservative over-approximation. The candidate sets from Phase 1, while safe, may contain anchors that are technically reachable but not semantically relevant. Therefore, in the second phase, the LLM acts as a sophisticated filter. For each subgoal sgjsg\_{j} and each structural anchor cic\_{i} in its candidate set, we prompt the LLM with the subgoal’s description and the anchor’s code. The LLM then determines whether the anchor is semantically and logically pertinent to achieving that specific subgoal, and prunes the mapping if it is not.

For instance, in the Pizza Onion quest, a version update may have modified (i) the logic for checking whether a dough on a counter already holds a valid tomato and cheese combination and (ii) refined the state transitions for chopped tomatoes and onions. These structural anchors are only relevant to specific subgoals such as “assemble a raw tomato pizza” and “bake the pizza in the oven,” and not to earlier steps like “place the dough on a counter.” Without structural-anchor mapping, the agents may repeatedly interact with the oven or attempt to place onions on plates before any dough or baked pizza is available. By contrast, our two-phase mapping can accurately identify (i) that dough-combination logic corresponds to the assembly subgoal and (ii) that oven-related logic corresponds to the baking subgoal in the Pizza Onion pipeline. (see Listing [6](https://arxiv.org/html/2512.12706v1#LST6 "Listing 6 ‣ Appendix ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning"))

### 3.7 Stage 5: Adaptive Hybrid Reward Function

The final stage is the adaptive hybrid reward function that orchestrates the agent’s learning process. Its primary goal is to train an agent to successfully execute the entire sequence of subgoals within a single episode, while simultaneously encouraging comprehensive exploration of all modified code across multiple episodes.

To achieve this, the function logic, detailed in Algorithm [1](https://arxiv.org/html/2512.12706v1#algorithm1 "In 3.7 Stage 5: Adaptive Hybrid Reward Function ‣ 3 Proposal ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning"), tracks two levels of state: an in-episode progress tracker (jj) that resets every episode, and a global coverage map (CcovC\_{cov}) that persists throughout the entire training process. At each step, it calculates a hybrid reward by checking for sequential subgoal completion against the reward sequence RR and for novel code coverage against the global map.

1

2

Input: Subgoal sequence

S\=(sg1,…,sgn)S=(sg\_{1},\\dots,sg\_{n})

Reward functions

R\=(r1,…,rn)R=(r\_{1},\\dots,r\_{n})

Structural anchors

CC

Reward magnitudes

rsem,rstrr^{sem},r^{str}

3

4Initialize global coverage map

Ccov←∅C\_{cov}\\leftarrow\\emptyset

5

6for _each episode e\=1,…,Ee=1,\\dots,E_ do

   // Reset environment

   // Reset in-episode subgoal index

   // Initialize trajectory buffer

7  

8   for _each step t\=0,…,T−1t=0,\\dots,T-1_ do

      // Agent selects an action

9     

(st+1,dt,Cstep)←env.step(at)(s\_{t+1},d\_{t},C\_{step})\\leftarrow\\text{env.step}(a\_{t})

     // Hybrid Reward Calculation

10     

rt←0r\_{t}\\leftarrow 0

11     

12      if _j≤nj\\leq n and rj(st+1)\>0r\_{j}(s\_{t+1})>0_ then

         // Semantic reward

         // Advance to next subgoal

13        

14       end if

15     

16      foreach _anchor cc in CstepC\_{step}_ do

17          if _c∉Ccovc\\notin C\_{cov}_ then

            // Structural reward

            // Mark covered anchor

18           

19          end if

20        

21       end foreach

22     

23      Store

(st,at,rt,st+1,dt)(s\_{t},a\_{t},r\_{t},s\_{t+1},d\_{t})

in

𝒟e\\mathcal{D}\_{e}

24       if _dtd\_{t}_ then

25          break

26        

27       end if

28     

29    end for

30   Update policy

π\\pi

using transitions in

𝒟e\\mathcal{D}\_{e}

;

31 end for

Algorithm 1 Adaptive Hybrid Reward Training Loop

To illustrate the algorithm’s dynamics, consider the pizza-making task. In an early episode, the agent’s primary motivation is to earn the sequential semantic rewards. It might learn to pick up a tomato and use the cutting board, which satisfies sg1sg\_{1} ("Obtain and chop a tomato"). Upon completion, the check at line 10 becomes true, the agent receives a large reward rsemr^{sem}, and its internal target advances to sg2sg\_{2} (the subgoal index jj is incremented to 2). During this process, it might cover a set of structural anchors {c1,c5,c8}\\{c\_{1},c\_{5},c\_{8}\\}. Since these are new, the check at line 14 is also true for each, granting additional rewards rstrr^{str} and adding them to the global CcovC\_{cov} map. The agent continues this process, learning a "happy path" to complete the entire quest.

Across many subsequent episodes, this learned "path" remains a reliable source of semantic rewards. However, the structural rewards along this path quickly diminish to zero, as {c1,c5,c8}\\{c\_{1},c\_{5},c\_{8}\\} and other anchors on this path are now in CcovC\_{cov}. To continue maximizing its total reward, the agent is intrinsically motivated to deviate from its routine. It might try chopping the tomato on a different cutting board in a different place, or interacting with another kitchen tool before chopping, to see if these actions lead to new outcomes. Such exploratory actions, while potentially delaying the semantic reward, are incentivized by the prospect of discovering an uncovered anchor (e.g., c12c\_{12}, an edge case in the chopping logic) and earning the rstrr^{str} bonus.

One concern of the adaptive hybrid reward design is the learning instability due to its unstable reward. Referring to the studies of Curiosity-driven RL \[[10](https://arxiv.org/html/2512.12706v1#bib.bib10)\], we address this challenge through several mechanisms. First, the semantic reward acts as a stable "backbone" for the learning process. It is consistently available in every episode, providing a clear and stationary objective that guides the agent towards a baseline level of functional competence. The structural reward, in contrast, serves as a diminishing bonus that catalyzes exploration without destabilizing the core policy. Second, we carefully balance the magnitudes of two types of rewards. By setting the one-time structural discovery bonus to be significant enough to incentivize deviation but not so large as to overshadow the cumulative semantic reward of completing the entire task, we manage the trade-off between exploration and exploitation. Finally, the underlying PPO algorithm itself incorporates mechanisms like entropy regularization, which intrinsically encourages policy stochasticity and prevents premature convergence, naturally complementing our external drive for exploration.

The adaptive structural reward calculation is realized through automated code instrumentation and tracking. We leverage standard dynamic analysis tools pytest to instrument the game’s source code before the training process begins. This instrumentation adds lightweight probes that record the execution of specific lines and control-flow branches without altering the core game logic. During runtime, when the agent performs an action and the game engine executes the corresponding code, these probes are triggered. The set of activated probes within a single step is collected and passed back to the RL environment through the ‘info’ dictionary. This allows the runtime engine to identify the set of newly covered anchors (info\[’covered\_anchors’\]info\[\\text{'covered\\\_anchors'}\]) in real time and compute the structural reward accordingly. This entire process is fully automated, requires no manual code modification, and introduces minimal calculation overhead.

## 4 Evaluation

The evaluation aims to answer the following two research questions:

-   •
    
    RQ1: Comprehensiveness and Effectiveness. How does the proposed SMART framework compare in terms of testing comprehensiveness and effectiveness against a range of baseline methods?
    
-   •
    
    RQ2: Efficiency and Cost. How does the SMART framework compare in terms of efficiency against baseline methods?
    
-   •
    
    RQ3: (Ablation Analysis): What are the respective contributions of the key components within the SMART framework to its overall performance?
    

### 4.1 Experiment Game Environment

![Refer to caption](https://arxiv.org/html/figures/games_v2.png)

Figure 2: Snapshots of the experimental game environments.

As shown in Figure [2](https://arxiv.org/html/2512.12706v1#S4.F2 "Figure 2 ‣ 4.1 Experiment Game Environment ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning"), we conduct experiments in two well-known games: Overcooked \[[11](https://arxiv.org/html/2512.12706v1#bib.bib11)\] and Minecraft \[[12](https://arxiv.org/html/2512.12706v1#bib.bib12)\] (Fig. [2](https://arxiv.org/html/2512.12706v1#S4.F2 "Figure 2 ‣ 4.1 Experiment Game Environment ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning")). Overcooked is a 2D simulation game centered on completing cooking tasks, where players act as chefs who interact with ingredients and kitchen tools to prepare various recipes. The game is widely celebrated for its cooperative design, earning multiple awards—including a BAFTA Games Award—and achieving significant commercial success with millions of copies sold. Given the closed-source nature of the original game, we employ its open-source experimental toolkit \[[13](https://arxiv.org/html/2512.12706v1#bib.bib13)\]. Minecraft is an open-world 3D sandbox game that allows players to freely explore, build, and dismantle structures. Since its release, it has become one of the best-selling games of all time and has cultivated a massive global player community, consistently praised for its creative and open-ended gameplay.

### 4.2 Experiment Settings

#### 4.2.1 Comparison Baseline Methods

We compare SMART against the following baselines.

Random Agent. This baseline represents a naive, uninformed exploration strategy, which is common in evaluating exploration strategies in complex environments \[[14](https://arxiv.org/html/2512.12706v1#bib.bib14)\].. At each timestep, the agent selects an action uniformly at random from the entire set of available actions in the environment. It serves as a lower bound on performance, illustrating the results achievable without any form of intelligent guidance.

PPO. This baseline represents a standard, task-oriented RL approach. We use PPO \[[15](https://arxiv.org/html/2512.12706v1#bib.bib15)\] , whose reward function is based solely on completing the quest. This agent is unaware of the underlying code changes and is only motivated to find an efficient policy to succeed at the task. It serves to demonstrate the performance of a pure "intent-only" testing paradigm. We utilize the robust implementation from the Stable-Baselines3 library \[[16](https://arxiv.org/html/2512.12706v1#bib.bib16)\].

PPO+ICM (Curiosity-Driven). This baseline augments the PPO with an Intrinsic Curiosity Module (ICM) \[[10](https://arxiv.org/html/2512.12706v1#bib.bib10)\]. The ICM provides an additional intrinsic reward to the agent for visiting novel states, which are defined as states that the agent’s internal forward dynamics model fails to predict accurately. This encourages the agent to explore unfamiliar parts of the state space, even if they do not directly contribute to the extrinsic task reward. This baseline represents a sophisticated, code-agnostic exploration strategy that aims to maximize state space coverage.

SMART (Ours and its Ablations) This category includes our full proposed framework and several ablated versions designed to isolate the contributions of its key components, particularly the hybrid reward structure.

-   •
    
    SMART (Full): This is the complete implementation of our proposed framework as described in Section [3](https://arxiv.org/html/2512.12706v1#S3 "3 Proposal ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning"). The agent is guided by the adaptive hybrid reward function, which combines both sequential semantic rewards for subgoal completion and adaptive structural rewards for discovering new code coverage.
    
-   •
    
    SMART (Semantic-Only): This ablation follows the same sequential curriculum of subgoals as the full method, but its reward function consists only of the semantic rewards (RsemR\_{sem}) for completing each subgoal in order. The entire structural reward component (RstrR\_{str}) is removed.
    
-   •
    
    SMART (Structural-Only): In this ablation, the agent’s reward function is based only on the adaptive structural reward (RstrR\_{str}) for covering previously unexecuted modified lines and branches. The semantic rewards for subgoal completion are completely removed.
    
-   •
    
    SMART (Global-Hybrid): This variant eliminates the hierarchical subgoal decomposition and the context-aware anchor mapping. Instead of a sequence of subgoals, the agent receives a semantic reward only upon the completion of the final quest (i.e., a sparse reward setting). Furthermore, the structural reward is globalized: the agent is incentivized to trigger any previously uncovered anchor from the entire set CC at any timestamp, without restricting coverage to specific gameplay stages.
    

#### 4.2.2 Settings in Overcooked

The evaluation of Overcooked is based on an open-source implementation \[[13](https://arxiv.org/html/2512.12706v1#bib.bib13)\], where the environment is a grid world with discrete actions (e.g., pick up tomato, chop ingredient, submit dish), and tasks are constructed according to real Overcooked recipes. The state space includes the player’s position, held items, and the status of environment objects. We simulate real-world game update cases and design two core element updates (“dough” and “oven”) from which 21 new tasks, approximately 200 lines of code differences, and around 100 branch differences are derived. (see Listing [8](https://arxiv.org/html/2512.12706v1#LST8 "Listing 8 ‣ Appendix ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning"))

In the Overcooked environment, each task is trained for up to 100,000 environment interactions, with a fixed episode horizon of 300 steps. To encourage efficient behavior, the agent receives a per-step penalty of –0.1. To ensure a balanced reward scale, the terminal reward for completing the quest is fixed at 200, while intermediate semantic rewards for subgoals range between 10 and 50 depending on the subgoal complexity. To ensure the consistency of underlying reinforcement learning algorithms across different methods, we adopt the reinforcement learning suite provided by the Python stable-baselines3 library. We use the default MlpPolicy as the policy model, set the learning rate to 3e-4, collect 2048 timesteps per rollout, and use a discount factor γ\=0.99\\gamma=0.99.

For PPO+ICM method, we incorporate an intrinsic-motivation signal based on state-visitation counts. At each step, the agent receives a curiosity bonus computed as rint(s)\=0.01N(s),r\_{\\text{int}}(s)=\\frac{0.01}{\\sqrt{N(s)}}, where N(s)N(s) denotes the number of times state ss has been visited. This intrinsic reward is added to the sparse extrinsic reward and jointly optimized via PPO to encourage exploration of novel states.

#### 4.2.3 Settings in Minecraft

The Minecraft environment is used to evaluate the scalability of the proposed method in a more complex open-world setting. The player starts from a fixed position and can execute parameterized high-level commands such as “mine,” “craft,” and “attack,” each of which is automatically decomposed into a sequence of atomic operations. The environment state includes the player’s position, inventory, and the dynamic states of spatial elements (e.g., resource blocks, furnaces, and enemies). We simulate real-world game update scenarios and design one core element update (“gold update”), from which 20 new tasks, approximately 180 lines of code differences, and around 100 branch differences are derived. (see Listing [7](https://arxiv.org/html/2512.12706v1#LST7 "Listing 7 ‣ Appendix ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning"))

For the Minecraft environment, we adopt the same reward shaping scheme but employ a larger training budget due to its more complex state and action spaces. Each task is allowed up to 1,000,000 environment interactions, with an episode horizon of 500 steps, while maintaining the same –0.1 per-step penalty. We’ve set the same reward levels as Overcooked, maintaining a base reward of 200 for completing the task, with interim rewards fluctuating between 10 and 50. Additionally, we employ the same Python stable-baselines3 library for reinforcement learning and keep the policy model and hyperparameters identical to those used in Overcooked.

### 4.3 Experiment Results and Discussion

Table 1: Comparative performance metrics on the Overcooked environment.

|       Method        | Line Coverage ↑\uparrow | Branch Coverage ↑\uparrow | Unique States ↑\uparrow | Ngram-3 Diversity ↑\uparrow | Anchor Discovery ↑\uparrow | Success Rate ↑\uparrow | Mean Length ↓\downarrow |
|---------------------|-------------------------|---------------------------|-------------------------|-----------------------------|----------------------------|------------------------|-------------------------|
|       Random        |      0.31±\pm0.01       |       0.35±\pm0.01        |   13,862.13±\pm238.73   |        63.39±\pm2.64        |       98.73±\pm1.75        |      0.06±\pm0.00      |     286.09±\pm6.69      |
|         PPO         |      0.55±\pm0.01       |       0.58±\pm0.01        |   23,171.25±\pm311.17   |        18.53±\pm0.19        |       165.43±\pm5.92       |      0.65±\pm0.02      |      45.49±\pm1.06      |
|       PPO+ICM       |      0.53±\pm0.00       |       0.55±\pm0.01        |  27,130.44±\pm1,306.04  |        37.02±\pm1.31        |       166.86±\pm3.87       |      0.62±\pm0.00      |      43.44±\pm0.18      |
|     SMART-Full      |      0.93±\pm0.02       |       0.98±\pm0.01        |   23,730.02±\pm676.49   |        28.86±\pm0.88        |       289.71±\pm1.40       |      0.98±\pm0.01      |      54.92±\pm2.26      |
|   SMART-Semantic    |      0.52±\pm0.02       |       0.61±\pm0.02        |   23,548.03±\pm14.10    |        20.85±\pm1.03        |       164.16±\pm8.02       |      0.96±\pm0.02      |      39.68±\pm0.47      |
|  SMART-Structural   |      0.31±\pm0.01       |       0.28±\pm0.01        |   13,754.21±\pm485.12   |        10.87±\pm0.19        |       90.19±\pm3.08        |      0.05±\pm0.00      |     286.50±\pm3.18      |
| SMART-Global-Hybrid |      0.29±\pm0.01       |       0.30±\pm0.03        |   14,486.92±\pm712.85   |        12.98±\pm0.13        |       95.37±\pm3.78        |      0.05±\pm0.01      |     282.41±\pm2.99      |

Table 2: Comparative performance metrics on the Minecraft environment.

|       Method        | Line Coverage ↑\uparrow | Branch Coverage ↑\uparrow | Unique States ↑\uparrow  | Ngram-3 Diversity ↑\uparrow | Anchor Discovery ↑\uparrow | Success Rate ↑\uparrow | Mean Length ↓\downarrow |
|---------------------|-------------------------|---------------------------|--------------------------|-----------------------------|----------------------------|------------------------|-------------------------|
|       Random        |      0.24±\pm0.01       |       0.19±\pm0.00        |  152,104.31 ±\pm 90.43   |        98.75±\pm3.09        |       64.12±\pm3.16        |      0.00±\pm0.00      |       501±\pm0.00       |
|         PPO         |      0.46±\pm0.01       |       0.51±\pm0.00        | 224,947.61 ±\pm 8,825.44 |        32.33±\pm1.33        |       145.29±\pm7.02       |      0.70±\pm0.03      |      48.26±\pm0.83      |
|       PPO+ICM       |      0.50±\pm0.01       |       0.51±\pm0.02        | 243,554.39 ±\pm 7,534.75 |        35.83±\pm1.42        |       149.43±\pm0.22       |      0.69±\pm0.03      |      54.81±\pm2.29      |
|     SMART-Full      |      0.92±\pm0.01       |       0.94±\pm0.01        | 210,947.41 ±\pm 3,804.29 |        22.23±\pm0.18        |       273.78±\pm3.32       |      0.98±\pm0.01      |      69.69±\pm1.65      |
|   SMART-Semantic    |      0.54±\pm0.03       |       0.52±\pm0.03        | 233,949.12 ±\pm 7,850.75 |        21.23±\pm0.34        |       159.19±\pm6.48       |      0.97±\pm0.01      |      47.68±\pm2.09      |
|  SMART-Structural   |      0.24±\pm0.00       |       0.16±\pm0.01        |  96,842.19 ±\pm 186.63   |        7.15±\pm0.08         |       67.79±\pm2.41        |      0.00±\pm0.00      |       501±\pm0.00       |
| SMART-Global-Hybrid |      0.25±\pm0.01       |       0.18±\pm0.03        | 118,163.18 ±\pm 3,899.65 |        14.74±\pm0.55        |       59.31±\pm0.71        |      0.00±\pm0.00      |       501±\pm0.00       |

The experimental results (see Table [1](https://arxiv.org/html/2512.12706v1#S4.T1 "Table 1 ‣ 4.3 Experiment Results and Discussion ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning") and Table [2](https://arxiv.org/html/2512.12706v1#S4.T2 "Table 2 ‣ 4.3 Experiment Results and Discussion ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning")) show the overall advantages of our proposal while revealing the fundamental limitations of traditional reinforcement learning in testing scenarios. Although PPO and PPO\_ICM achieve a reasonable level of task success rate (approximately 0.7), their line coverage remains at only 0.46–0.55, and their mean anchor discovery is extremely low. This indicates that task-oriented agents tend to complete tasks via the “shortest path,” thereby systematically ignoring the non-critical paths (edge cases) introduced during updates. In contrast, SMART\-Full, utilizing a hybrid reward mechanism, increases both line and branch coverage to 0.9/0.95. This strongly demonstrates the core idea of our proposal that only by explicitly incorporating code structure changes into the reward function can the agent be truly guided into the “code space” under test.

Regarding the performance of the curiosity mechanism (ICM), although PPO\_ICM achieves a slightly higher number of unique states (27.1k) than SMART (as shown in Table [1](https://arxiv.org/html/2512.12706v1#S4.T1 "Table 1 ‣ 4.3 Experiment Results and Discussion ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning")), its discovery rate for new code (166.86) is much lower than that of SMART. This suggests a mismatch between “state novelty” and “code novelty”: ICM encourages the agent to explore visually distinct or dynamically unpredictable states (such as running around the map or viewing different scenery), but these states do not necessarily correspond to the modified code branches in the current code update (about 200 lines of diff). Therefore, blindly maximizing state diversity is an inefficient strategy for testing specific code updates. In contrast, SMART’s exploration is “constrained and precise”: although the total number of states it visits is slightly lower, every new state explored closely revolves around code change points (anchors). This demonstrates that, in incremental testing scenarios, code-aware directed exploration (coverage-aware exploration) is far more cost-effective than generic exploration based on pixel or state prediction error (curiosity-driven exploration). Additionally, with regard to Ngram-3 diversity, Random is the strongest, followed by ICM, indicating that mere diversity in action sequences does not directly translate into effective testing of updated code. Ablation studies further analyze the contributions of each component. First, as shown by the distribution in Figure [3](https://arxiv.org/html/2512.12706v1#S4.F3 "Figure 3 ‣ 4.3 Experiment Results and Discussion ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning"), SMART - Semantic achieves a high success rate (about 97%) and the shortest average trajectory length, but its code coverage is significantly lower than that of the full method (for example, 52% line coverage vs. 93% in Overcooked). This result actually highlights the “happy path” problem: while LLM-generated semantic rewards can perfectly guide the agent to complete the task, they often lead it down the most standard and efficient path, effectively bypassing error-handling logic, boundary checks, and other defensive programming regions.

In contrast, the complete failure of SMART - Structural (with both success rate and coverage near random levels, and frequent timeouts, see Table [2](https://arxiv.org/html/2512.12706v1#S4.T2 "Table 2 ‣ 4.3 Experiment Results and Discussion ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning")) confirms that the “reachability” of deep code logic heavily depends on high-level game context. Without semantic subgoal guidance from the LLM, the agent cannot construct long sequences of dependent actions, resulting in code logic deeply embedded at the backend of the task being physically unreachable.

Equally noteworthy is the poor performance of SMART - Global-Hybrid. Although this variant retains both semantic goals and structural reward signals, its results (low success rate and coverage comparable to random) further validate the necessity of goal decomposition and context mapping. Without decomposing complex tasks into a sequence of subgoals, agents struggle to overcome the challenge of sparse rewards; and lacking context mapping to structural anchors, global code coverage rewards become too sparse and lack directionality. This indicates that a simple additive combination of “functional + structural” rewards is ineffective. Only the fine-grained alignment proposed by SMART enables structural signals to truly assist functional exploration.

Finally, the full method (SMART - Full) results in slightly longer trajectories than the semantic-only variant (e.g., 69.69 vs. 47.68 in Minecraft), but with significantly higher coverage. This increase in trajectory length represents “productive inefficiency”: the structural reward mechanism successfully incentivizes the agent to deviate from the optimal path and perform exploratory actions (such as trying different tools or materials), thereby triggering edge-case code. In traditional RL tasks, an increase in steps is usually regarded as a performance decline, but in testing scenarios, this deliberately extended trajectory essentially reflects the agent trading time cost for higher anchor discovery (as shown in Figure [4](https://arxiv.org/html/2512.12706v1#S4.F4 "Figure 4 ‣ 4.3 Experiment Results and Discussion ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning")), which is precisely the behavior pattern desired in automated testing to balance functional and structural verification.

![Refer to caption](https://arxiv.org/html/figures/evaluation/combined/3.png)

Figure 3: Detailed distribution of structural coverage and task success rates.

Figure [3](https://arxiv.org/html/2512.12706v1#S4.F3 "Figure 3 ‣ 4.3 Experiment Results and Discussion ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning") further presents box plots of structural coverage and success rates under different task granularities. A detailed analysis of the statistical features in this figure yields two key conclusions. First, the performance advantage of SMART demonstrates a high degree of universality, i.e., SMART achieves significantly higher code line and branch coverage across the vast majority of individual tasks. Second, SMART exhibits robustness, i.e., observing the interquartile range of the box plots, SMART shows a compact coverage distribution and a high lower quartile, indicating the absence of obvious “bottleneck” tasks in the test set. Even when faced with tasks involving complex logic or intricate interaction steps—which are typically blind spots for methods like PPO—SMART is able to maintain a high level of structural coverage.

![Refer to caption](https://arxiv.org/html/figures/evaluation/combined/2.png)

Figure 4: Learning curves for cumulative structural anchor coverage.

Figure [4](https://arxiv.org/html/2512.12706v1#S4.F4 "Figure 4 ‣ 4.3 Experiment Results and Discussion ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning") depicts the growth trend of the cumulative number of unique code anchors covered as the number of test tasks increases (tasks are sorted by ascending complexity). It is evident that SMART features the steepest growth curve, indicating that for each new test task introduced, SMART can efficiently discover a large number of previously untriggered code logic branches. In contrast, baseline methods encounter an early “plateau,” suggesting a tendency to reuse existing simple interaction patterns (happy paths) when facing new tasks, which makes it difficult to reach deep code branches unique to the new tasks. Furthermore, as task complexity increases (rightward along the X-axis), the gap between SMART and the baselines widens, reaffirming that SMART holds significant scalability advantages in incremental development settings.

Although SMART achieves significantly higher coverage than baseline methods in both game environments, its final coverage still falls short of the theoretical 100%, as illustrated in Figure [4](https://arxiv.org/html/2512.12706v1#S4.F4 "Figure 4 ‣ 4.3 Experiment Results and Discussion ‣ 4 Evaluation ‣ Synergizing Code Coverage and Gameplay Intent: Coverage-Aware Game Playtesting with LLM-Guided Reinforcement Learning"). We conducted an in-depth code-level review of these uncovered anchors and identified two main contributing factors. First, some of the structural anchors identified by AST differencing correspond to extreme defensive programming or exception-handling logic. For example, in the “Onion Pizza” task of Overcooked, certain uncovered code sections pertain to protective checks for “illegal ingredient stacking order” or “forced interaction after prolonged idle baking.” Guided by the normal task semantics and LLM-generated subgoals, the agent’s behavior remains within logical bounds, and thus rarely triggers these fallback mechanisms designed to prevent program crashes. Second, this outcome represents a necessary trade-off between training efficiency and exploration depth. Under constraints of limited training steps and per-step penalties, PPO-based strategies naturally converge to paths with more stable reward returns. Although our structural reward (RstrR\_{str}) provides strong incentives for exploratory behaviors, systematically covering all edge-case branches (e.g., deliberately waiting until a timeout to trigger an error prompt) may lead the agent to frequently deviate from the task objective, significantly reducing training efficiency and destabilizing policy convergence. Thus, SMART is designed to maximize structural coverage while ensuring thorough testing of the main functional paths and common interaction logic, rather than pursuing exhaustive coverage of all dead code or unreachable logic at any cost. To address these residual blind spots, a promising solution is to integrate SMART with fuzz testing or symbolic execution techniques. While SMART excels at verifying complex, long-dependency gameplay logic, these complementary techniques can “brute-force” trigger counter-intuitive defensive branches and exception-handling code via constraint solving or random mutation. Together, they can construct a comprehensive automated testing framework that covers both happy paths and edge cases.

### 4.4 Limitations

Although our proposed SMART framework demonstrates promising results in synergizing structural code with functional gameplay validation, several methodological limitations warrant discussion.

First, the effectiveness of our framework is highly dependent on the quality and accuracy of the semantic intent generated by the LLM. The core innovation of SMART lies in its ability to translate low-level code modifications into high-level, testable gameplay objectives. However, If the LLM misinterprets the purpose of a code change—for example, by hallucinating a gameplay feature from a simple refactoring, or failing to capture the subtle nuances of a balance adjustment—the resulting semantic reward function may be misaligned. A flawed semantic reward could potentially drive the RL agent toward irrelevant or incorrect behaviors, thus undermining the very synergy between structural and functional testing that SMART aims to achieve.

Second, similar to existing agent-based testing methods, this paper focuses on testing updates to the core gameplay logic of the game. Therefore, we employ AST analysis, which excels at identifying modifications in control flow, data structures, and algorithmic computations. However, we acknowledge that modern games are increasingly complex and data-driven. For example, changes to user interface (UI) layouts defined in XML files, adjustments to 3D model assets, modifications in shader code for graphical effects, or tweaks in neural network-based AI behavior often do not manifest as interpretable changes in the primary source code’s AST. Updates outside the core game logic thus require complementary techniques from other domains to be effectively tested.

Third, it is important to emphasize that SMART is designed for frequent, incremental testing rather than as a comprehensive replacement for the thorough validation required in major releases. As previous work notes, robust quality assurance—especially for large updates—relies on a combination of regression testing, performance profiling, and manual exploratory testing to ensure overall game stability \[[3](https://arxiv.org/html/2512.12706v1#bib.bib3)\]. While SMART focuses on change deltas and does not achieve exhaustive system-wide verification, it provides unique value when integrated into a broader testing pipeline. Specifically, SMART offers two key contributions: First, it acts as an intelligent, automated smoke test, rapidly validating the most critical functionalities affected by updates. This gives QA teams an early signal of build stability before committing to full regression cycles. Second, the test trajectories generated by the SMART agent serve as high-quality, machine-generated assets that already validate new features. These trajectories can be curated and optimized to seed new regression test cases, accelerating the maintenance of the test suite and reducing the manual effort required to create new validation scenarios from scratch.

Fourth, we specifically focus on the element addition scenario in the experiment, as the introduction of new gameplay elements and associated quests constitutes the most frequent and representative update pattern in the GaaS model. Although real game version updates typically involve substantial and diverse content changes, this decision is grounded in operational reality and based on two considerations: First, existing automated game testing baselines, particularly those agent-based methods, are generally designed and evaluated for a specific, singular game task or quest. By restricting the experiment to tasks triggered by element update, we can eliminate interference from multi-task scheduling, thereby allowing for a more precise and fair comparison with baseline methods in terms of structural coverage and functional completion on the same dimension. Second, rather than focusing on external version updates, our method assumes an internal Continuous Integration (CI) process. In this context, "Gameplay Intent" is not monolithic but composed of discrete functional goals. A single code commit typically involves a small number of changes (such as adding a new element and its corresponding quests), representing an atomic unit of gameplay intent. Since a large studio may execute dozens of such commits daily, testing a single element update corresponds to verifying the most fundamental and frequent unit of intent. Therefore, ensuring the completion of the specific task associated with the code update is effectively validating the "Gameplay Intent" inherent in that specific increment. To address complex externally released updates that combine multiple elements, a natural extension strategy is "hierarchical decomposition and code anchoring," which involves decomposing a large update into multiple such atomic units.

Fifth, the design of the hybrid reward function introduces a significant challenge in balancing the structural and semantic reward components. Specifically, the relative weighting of these two signals is non-trivial and may be highly context-dependent. An imbalance could lead the agent to "game" the system; for instance, it might prioritize executing many shallow code paths to maximize the structural reward, while failing to adequately validate the complex, multi-step functional intent of an update. This may require careful, per-update tuning of reward weights, which could introduce a layer of manual oversight and potentially compromise the framework’s full automation. Future work could explore more advanced reward-shaping mechanisms to address this challenge dynamically.

Finally, our reliance on AST-based static analysis inherently limits the detection of dynamic code behaviors. Modern game engines often utilize reflection, dynamic asset loading, or hot-swapped scripts (e.g., Lua or Python) whose control flow cannot be fully resolved statically. If a game update relies heavily on such dynamic dispatch mechanisms, the structural anchor mapping in Stage 4 may fail to identify or link these code paths to the correct subgoals. Therefore, it is also a promising direction to integrate dynamic call-graph generation to complement the static AST differencing.

## 5 Related Work

This section reviews two core research directions in the field of automated game testing, and discusses the position of this study.

### 5.1 Structural Game Testing

With the rise of the GaaS, games require frequent content updates and feature iterations, making regression testing an indispensable part of software quality assurance \[[2](https://arxiv.org/html/2512.12706v1#bib.bib2)\]. The goal of regression testing is to verify that new code changes do not inadvertently break existing functionality.

Early automation efforts mainly focused on record-and-replay and script-based testing. The record-and-replay mechanism captures human testers’ action sequences and transforms them into reusable test cases, reducing repetitive labor \[[17](https://arxiv.org/html/2512.12706v1#bib.bib17), [18](https://arxiv.org/html/2512.12706v1#bib.bib18)\]. Similarly, script-based testing relies on testers writing control scripts to simulate player behavior, which is suitable for verifying fixed game scenarios and task flows \[[19](https://arxiv.org/html/2512.12706v1#bib.bib19), [20](https://arxiv.org/html/2512.12706v1#bib.bib20)\]. However, both approaches have significant limitations. They are heavily reliant on manual creation and maintenance of test assets; when game UIs or functional logic change, these scripts or recorded traces often become invalid, resulting in high maintenance costs \[[21](https://arxiv.org/html/2512.12706v1#bib.bib21)\].

To improve regression testing efficiency, researchers have introduced more advanced Regression Test Selection (RTS) techniques, whose core idea is to execute only the test cases potentially affected by code changes \[[22](https://arxiv.org/html/2512.12706v1#bib.bib22)\]. For instance, GameRTS \[[23](https://arxiv.org/html/2512.12706v1#bib.bib23)\] constructs a game state transition graph through static code analysis, and after version updates, it intelligently identifies the most relevant test cases for re-testing by analyzing code differences. This approach effectively avoids unnecessary test executions while maintaining a high defect detection rate.

However, these code-centric regression testing methods have a fundamental limitation: they focus on structural verification but lack an understanding of functional intent. For example, in a cooking game like Overcooked, an update might modify the interact function to support a new “chopping” mechanic for tomatoes. An RTS tool can accurately identify this code change and select a generic test case where the avatar simply triggers the interaction button. Nevertheless, it cannot determine the underlying intent—whether the interaction is meant to transform a whole tomato into a chopped state as part of a new “Pizza” recipe, or simply to pick up the item. Consequently, it cannot select test scenarios specifically aimed at verifying if the chopping action actually progresses the specific culinary task or if the state transition logic functions correctly within the recipe workflow. These methods can only confirm that the code structure has been exercised, but cannot verify whether the intended higher-level gameplay goals of the structural changes have been achieved.

### 5.2 Intent-Driven Game Testing

To overcome the rigidity and high maintenance costs of traditional script-based methods, the research community has gradually shifted towards using agents capable of autonomously interacting with the environment for game testing. This approach emphasizes exploratory testing, aiming to discover unintended behaviors and edge cases.

Early agent-based methods include model-based testing, where a formal model of gameplay is constructed in advance, and agents generate test paths according to the model \[[24](https://arxiv.org/html/2512.12706v1#bib.bib24), [25](https://arxiv.org/html/2512.12706v1#bib.bib25)\]. Additionally, behavior trees have been used to build agents for level evaluation and playability analysis \[[26](https://arxiv.org/html/2512.12706v1#bib.bib26), [27](https://arxiv.org/html/2512.12706v1#bib.bib27)\]. These methods offer more flexibility than fixed scripts but still require substantial upfront design and modeling effort.

The emergence of RL has brought a paradigm shift to automated game testing. RL agents learn gameplay through trial-and-error, without the need for predefined scripts or models, making them highly suitable for exploring vast and dynamic game worlds \[[28](https://arxiv.org/html/2512.12706v1#bib.bib28)\]. To enhance the efficiency and breadth of exploration, researchers have proposed various augmentations. Among these, curiosity-driven approaches introduce intrinsic rewards to incentivize agents to visit novel or unexplored game states, thereby significantly improving state-space coverage and the ability to uncover hidden defects \[[29](https://arxiv.org/html/2512.12706v1#bib.bib29)\]. Moreover, some studies combine deep reinforcement learning with evolutionary strategies, evolving diverse agent policies to balance task completion and state exploration, which has shown promising results in complex online battle games, such as the Wuji framework \[[30](https://arxiv.org/html/2512.12706v1#bib.bib30)\]. To make agent behavior more closely resemble real players, persona-based testing has been developed. By assigning agents different predefined personas (e.g., “explorer” or “achiever”) and designing corresponding reward functions, agents are guided to execute test paths aligned with specific motivations \[[31](https://arxiv.org/html/2512.12706v1#bib.bib31), [32](https://arxiv.org/html/2512.12706v1#bib.bib32)\].

Although these agent-based methods excel at simulating player behavior and functional validation, they typically operate at the intent level and lack direct connections to underlying structural changes. Most run in black-box or gray-box environments, with behavior driven by high-level game feedback (e.g., scores, task completion status). A fundamental limitation of this reward-driven approach is the agent’s tendency to converge on a single optimal strategy, often referred to as the Happy Path.” For instance, an RL agent trained to complete a cooking quest will learn the most efficient sequence of actions to deliver a dish. Consequently, it will systematically avoid suboptimal interactions or erroneous states—such as burning an ingredient or combining invalid items—effectively bypassing the very defensive programming and exception-handling logic introduced in the code update. As a result, while the agent proves the task is clearable, it fails to exercise the alternative branches and edge cases that constitute a significant portion of the structural changes.

### 5.3 Position of This Paper

The preceding review highlights a key dichotomy in current game testing methodologies: the gap between low-level structural verification and high-level functional/intent validation. Traditional regression testing approaches \[[23](https://arxiv.org/html/2512.12706v1#bib.bib23), [17](https://arxiv.org/html/2512.12706v1#bib.bib17)\] excel at analyzing changes from the code perspective and conducting structural testing, but they are unable to comprehend the higher-level functional intent behind code modifications, nor can they proactively verify whether these intents have been correctly implemented. In contrast, agent-based exploratory or behavior-driven testing \[[29](https://arxiv.org/html/2512.12706v1#bib.bib29), [30](https://arxiv.org/html/2512.12706v1#bib.bib30), [33](https://arxiv.org/html/2512.12706v1#bib.bib33)\] focuses on simulating player behavior and validating functionality. However, due to the lack of direct association with underlying code changes, these methods cannot guarantee effective coverage of specific code modifications, and thus may miss regression defects that affect only code structure without immediately altering macro-level behavior.

The SMART framework proposed in this study aims to systematically bridge this critical gap. Unlike previous work, SMART does not merely utilize LLMs for general game task planning \[[14](https://arxiv.org/html/2512.12706v1#bib.bib14), [34](https://arxiv.org/html/2512.12706v1#bib.bib34)\] or test case generation \[[35](https://arxiv.org/html/2512.12706v1#bib.bib35), [36](https://arxiv.org/html/2512.12706v1#bib.bib36), [37](https://arxiv.org/html/2512.12706v1#bib.bib37)\]. Instead, the core novelty SMART lies in directly grounding itself in the most fundamental structural changes—source code differences (AST diff)—and leveraging the powerful semantic understanding capabilities of LLMs to automatically reverse-engineer and interpret the high-level functional intent behind these structural modifications. Building upon this, SMART introduces a novel hybrid reward function that integrates both the structural coverage reward derived from code changes and the semantic intent reward inferred by LLMs. This mechanism ensures that reinforcement learning agents are not only incentivized to execute all modified code paths but are also guided to align their behavior with the higher-level functional goals implied by these changes.

## 6 Conclusion and Future Work

In this paper, we proposed SMART, a novel automated testing framework that synergizes code coverage with gameplay intent. By leveraging LLMs to interpret AST differences and decomposing them into semantic subgoals, SMART constructs a context-aware hybrid reward system. This system guides RL agents to not only fulfill the functional requirements of new game updates but also to actively explore and cover the underlying structural modifications. Our experiment evaluation on Overcooked and Minecraft demonstrates that SMART significantly outperforms traditional RL and curiosity-driven baselines, achieving an extremely high coverage of modified code branches while maintaining high task success rates.

In future work, we plan to expand SMART in three directions. First, we aim to implement a closed-loop refinement mechanism to mitigate the impact of LLM hallucinations in one-off subgoals and rewards. Specifically, we plan to introduce an iterative cycle where the agent’s failure trajectories or low-coverage reports are fed back to the LLM, allowing it to dynamically debug and refine its generated semantic rewards and anchor mappings, thereby improving robustness against ambiguous code changes. Second, we aim to address the challenge of non-code updates by incorporating multi-modal analysis, allowing the framework to test changes in game assets, UI layouts, and data tables that do not manifest in the AST. Finally, acknowledging the trade-off between RL exploration and deep defensive logic coverage, we will explore hybridizing SMART with symbolic execution or fuzz testing.

## Appendix

This appendix provides detailed prompts, output examples from the SMARTframework stages, and the exmaple lists of tasks used in the experiments.

{

"system\_role": "You are a subgoal generator and structural anchor annotator.",

"task\_description": {

"summary": "Given an AST difference report (ast\_diff.txt) generated by a static analysis tool, identify newly added or significantly expanded game tasks, decompose them into ordered subgoals, and annotate each subgoal with structural anchors.",

"steps": \[

"Identify newly added or significantly expanded game tasks.",

"Decompose each complex task into an ordered sequence of subgoals S \= (sg1, ..., sgN), where each subgoal is a natural\-language description, verifiable, and relatively atomic.",

"Annotate each subgoal with structural anchors\-specific code locations directly related to that subgoal."

\]},

"input\_data": {

"source": "AST difference report file (ast\_diff.txt) generated by a static analysis tool.",

"content\_format": "Text diff containing module headers and unified diff lines.",

"ast\_diff\_wrapper": {

"begin\_marker": "===== BEGIN AST DIFF \=====",

"end\_marker": "===== END AST DIFF \=====",

"placeholder": "{ast\_diff\_text}"},

"module\_header\_example": "== Module: controller/action.py \==",

"line\_type\_description": {

"added\_lines": "Lines beginning with ’+’ (new version). Prefer these as anchors.",

"removed\_lines": "Lines beginning with ’-’ (old version). Use only when describing removed behavior."}},

"task\_definitions": {

"new\_or\_expanded\_task": "A new task or a significantly expanded existing task inferred from the AST diff. Tasks generally correspond to noticeable flows, gameplay steps, crafting recipes, combat logic, or prerequisite logic.",

"subgoal": {

"description": "A subgoal is an ordered step within a task, described in natural language, with clear verifiable conditions and relatively atomic behavior.",

"requirements": \[

"Natural\-language description.",

"Verifiable in code or gameplay logic.",

"Relatively atomic (should not require further splitting into independent steps)."\]},

"structural\_anchor": {

"description": "A structural anchor is a set of code locations most directly related to a subgoal.",

"format": "(file\_path, line\_number\_array) pairs, where file\_path comes from module headers and line\_number\_array uses unified diff line numbers."}},

"output\_requirements": {

"overall": "For each new or expanded task, produce an object containing ordered subgoals and their structural anchors.",

"task\_object": {

"fields": \[

"task\_id: A unique string identifying the task (derived from code context or inferred task name).",

"subgoals: An ordered list of subgoal descriptions.",

"anchors: An array aligning with subgoals by index, each containing code anchor locations."\]},

"subgoal\_properties": \[

"Ordered: sg1 \-> sg2 \-> ... \-> sgN follow the completion sequence.",

"Logical dependency: Later subgoals typically require earlier ones.",

"Natural\-language text."

\],

"structural\_anchor\_rules": {

"anchor\_format": "(file\_path, line\_number\_array)",

"file\_path": "From diff module headers (e.g., ’controller/action.py’).",

"line\_numbers": "From unified diff lines starting with ’+’ or ’-’; prefer ’+’.",

"span\_rules": \[

"Use \[start, end\] for multi\-line spans, e.g., \[424, 431\].",

"Use a single\-element array for single lines, e.g., \[188\]."\],

"selection\_preference": \[

"Prefer core logic: material requirements, action logic, crafting tables, attack logic, prerequisite checks, etc.",

"Provide 2~5 anchors per subgoal; only leave empty when absolutely necessary."\]},

"json\_output\_format": {

"description": "Output must be a single JSON object. Example:",

"template": {

"tasks": \[{

"task\_id": "Craft\_Iron\_Sword",

"subgoals": \["Subgoal 1", "Subgoal 2"\],

"anchors": \[

{"index": 0, "text": "Subgoal 1", "locations": \[

{"file": "env/vector.py", "span": \[424, 431\]},

{"file": "controller/action.py", "span": \[172, 182\]}

\]},

{"index": 1, "text": "Subgoal 2", "locations": \[

{"file": "env/vector.py", "span": \[461, 476\]}

\]}\]}\]}}},

"constraints": {

"anchors\_per\_subgoal": {

"min": 2, "max": 5,

"note": "Leave empty only when anchor lines cannot be identified."},

"line\_usage\_preference": \[

"Prefer ’+’ (new) version line numbers.",

"Use ’-’ only when describing removed behavior."

\],

"mapping\_precision": "Anchors should precisely correspond to the implementation logic of each subgoal.",

"language": "All subgoals must be written in natural language.",

"format\_adherence": "Output must be strictly the specified JSON object without additional commentary."

},

"examples": {

"intuitive\_examples": \[

"Pizza: cut tomatoes \-> make sauce \-> assemble pizza \-> bake pizza",

"Craft\_iron\_Sword: collect wood \-> obtain iron ore \-> smelt iron \-> craft iron sword"

\],

"note": "Actual subgoals must be strictly inferred from the AST diff ({ast\_diff\_text})."

}

}

Listing 1: Prompt for Subgoal Generation (Stage 2).

{

"system\_role": "You are a reward\-function generation assistant, specialized in designing appropriate reward functions for game tasks.",

"task\_description": "You will receive a task, its subgoals, and various information extracted from the game code. Based on these inputs, you must generate multiple reward functions that guide the agent toward completing the task.",

"input\_data": {

"description": "The input consists of a task ID, a list of subgoals, an item list, and a task list. These are injected into the placeholders {task\_id}, {subgoals}, {ITEMS}, and {TASK\_IDS}.",

"example": {

"task\_id": "task\_001",

"subgoals": \["collect wood", "craft axe", "cut trees"\],

"ITEMS": \["wood", "stone", "axe"\],

"TASK\_IDS": \["subtask\_1", "subtask\_2", "subtask\_3"\]}},

"output\_instructions": {

"format": "You must generate a strict JSON object containing the target task ID and a list of reward definitions.",

"json\_template": {

"target\_task\_id": "{task\_id}",

"rewards": \[{"items": \[\["item\_name", 1\]\], "reward": 10},

{"task": "subtask\_id", "reward": 15}\]}},

"critical\_constraints": \[

{"constraint": "Full Process Coverage", "description": "Reward functions must cover the entire task process, from beginning to completion."},

{"constraint": "Item\-Based Reward Logic", "description": "For item\-triggered rewards, the reward activates only when the inventory simultaneously contains all specified items in the required amounts."},

{"constraint": "Subtask\-Based Reward Logic", "description": "For subtask\-triggered rewards, the reward activates upon completion of the specified subtask. You may include rewards for prerequisite subtasks to guide the agent."},

{"constraint": "Once\-Only Trigger", "description": "Each reward triggers only once. The agent incurs a 0.1 penalty per step."},

{"constraint": "Granularity", "description": "Use fine\-grained rewards to guide incremental progress. Staged rewards are allowed when collecting multiple quantities of items."},

{"constraint": "Reward Scale", "description": "Main task reward is fixed at 200. Sub\-rewards should range between 10 and 50."},

{"constraint": "Format Adherence", "description": "Output must be strictly in JSON format, without any additional commentary."}

\]

}

Listing 2: Prompt for Semantic Reward Generation (Stage 3).

{

"system\_role": "You are an anchor alignment assistant responsible for aligning subgoals in Minecraft tasks to specific code change locations (file path and line number ranges).",

"task\_description": "Use the provided code\-reading tools to verify project structure and code changes, and map each task subgoal to precise code locations in the modified Python source files. All line numbers must come from actual tool outputs; no imaginary code or invented spans are allowed.",

"tools\_description": {

"tree\_project": "View the Python file tree of the project. Some irrelevant files such as pppo.py and env/vector.py may be excluded automatically.",

"read\_file": "Read the content of a Python source file by its relative path.",

"search\_project": "Search for a string across all Python files and return matches with surrounding context.",

"list\_diffs": "List the modules changed in this round of code modifications.",

"file\_diff": "Display a human\-readable AST diff of a module, showing added, modified, or removed functions and fields, along with their old and new line numbers.",

"change\_spans": "Given a module path and a symbol name, return the old and new line\-number spans (span\_old / span\_new)."

},

"output\_instructions": {

"format": "Produce a JSON object describing the code locations corresponding to each subgoal of the current task.",

"json\_template": {

"task\_id": "<current task ID\>",

"subgoals": \[{

"index": 0,

"text": "original subgoal text (copied verbatim)",

"locations": \[{

"file": "path/to/file.py",

"span": \[10, 11, 12\],

"kind": "function or non\_function (optional)",

"change\_type": "added / modified / removed (optional)",

"symbol": "function\_or\_variable\_name (optional)",

"qualname": "fully.qualified.name (optional)"

}\]}\]}},

"critical\_constraints": \[

{"constraint": "Do Not Invent Code", "description": "All file paths and line number spans must come from tool results such as change\_spans or file\_diff."},

{"constraint": "Accurate Span Usage", "description": "The span field must contain new\-version line numbers. Prefer using line\_numbers\_new from change\_spans whenever possible."},

{"constraint": "Faithful Subgoal Mapping", "description": "Subgoals must be copied verbatim, and each mapped location must correspond to verified code changes relevant to that subgoal."},

{"constraint": "Empty Allowed", "description": "If no code change corresponds to a subgoal, the locations list may be empty."},

{"constraint": "JSON\-Only Output", "description": "The final response must contain only the required JSON object, with no extra commentary."}

\],

"notes": \[

"Subgoal indices start from 0.",

"Use the tools to fully understand the code before generating the final JSON.",

"env/vector.py will not appear in list\_diffs, even if changed.",

"Prioritize change\_spans for accurate symbol\-level line ranges."\]

}

Listing 3: Prompt for Structural Anchor Mapping (Stage 4).

{"tasks": \[{"task\_id": "pizza\_onion",

"subgoals": \["Pick up a clean plate from a plate tile.",

"Pick up a dough from a dough tile and place it on a counter so it can be used as a pizza base.",

"Pick up a tomato from a tomato tile, bring it to a knife tile, and chop it until the chop progress is complete.",

"Pick up cheese from a cheese tile and place both chopped tomato and cheese onto the dough on the counter so that the plate can later contain a pizza.",

"Pick up the raw pizza on a plate and put it into an oven tile; wait until the cooked flag of the pizza becomes true without letting it burn.",

"Take the cooked pizza out of the oven on a plate and, if the map provides onion, optionally chop onion on a knife and add it onto the same plate as an extra topping.",

"Deliver the plate with the finished pizza (and any extra toppings such as onion) at a delivery tile so that TaskManager marks the task as correctly completed."\],

"anchors": \[{"index": 0, "text": "Pick up a clean plate from a plate tile.",

"locations": \[{"file": "overcooked/overcookedPlus/module/item\_manager.py", "span": \[55, 118\]},

{"file": "overcooked/overcookedPlus/items.py", "span": \[682, 780\]},

{"file": "overcooked/overcookedPlus/module/event\_manager.py", "span": \[180, 260\]}\]},

{"index": 1, "text": "Pick up a dough from a dough tile and place it on a counter so it can be used as a pizza base.",

"locations": \[{"file": "overcooked/overcookedPlus/module/item\_manager.py", "span": \[60, 130\]},

{"file": "overcooked/overcookedPlus/items.py", "span": \[260, 340\]},

{"file": "overcooked/overcookedPlus/module/event\_manager.py", "span": \[320, 480\]}\]},

{"index": 2, "text": "Pick up a tomato from a tomato tile, bring it to a knife tile, and chop it until the chop progress is complete.",

"locations": \[{"file": "overcooked/overcookedPlus/module/item\_manager.py", "span": \[40, 90\]},

{"file": "overcooked/overcookedPlus/items.py", "span": \[120, 220\]},

{"file": "overcooked/overcookedPlus/module/event\_manager.py", "span": \[520, 620\]}\]},

{"index": 3, "text": "Pick up cheese from a cheese tile and place both chopped tomato and cheese onto the dough on the counter so that the plate can later contain a pizza.",

"locations": \[{"file": "overcooked/overcookedPlus/module/item\_manager.py", "span": \[70, 150\]},

{"file": "overcooked/overcookedPlus/items.py", "span": \[220, 320\]},

{"file": "overcooked/overcookedPlus/items.py", "span": \[780, 980\]}\]},

{"index": 4, "text": "Pick up the raw pizza on a plate and put it into an oven tile; wait until the cooked flag of the pizza becomes true without letting it burn.",

"locations": \[{"file": "overcooked/overcookedPlus/module/item\_manager.py", "span": \[80, 170\]},

{"file": "overcooked/overcookedPlus/items.py", "span": \[320, 420\]},

{"file": "overcooked/overcookedPlus/module/event\_manager.py", "span": \[1040, 1240\]}\]},

{"index": 5, "text": "Take the cooked pizza out of the oven on a plate and, if the map provides onion, optionally chop onion on a knife and add it onto the same plate as an extra topping.",

"locations": \[{"file": "overcooked/overcookedPlus/module/item\_manager.py", "span": \[40, 160\]},

{"file": "overcooked/overcookedPlus/items.py", "span": \[180, 300\]},

{"file": "overcooked/overcookedPlus/module/event\_manager.py", "span": \[1240, 1540\]}\]},

{"index": 6, "text": "Deliver the plate with the finished pizza (and any extra toppings such as onion) at a delivery tile so that TaskManager marks the task as correctly completed.",

"locations": \[{"file": "overcooked/overcookedPlus/module/item\_manager.py", "span": \[40, 120\]},

{"file": "overcooked/overcookedPlus/module/task\_manager.py", "span": \[80, 220\]},

{"file": "overcooked/overcookedPlus/module/event\_manager.py", "span": \[260, 360\]}\]}\]}\]}

Listing 4: Example Output of Subgoal Sequence (Stage 2).

{"task\_id": "pizza\_onion", "description": "Cook a tomato\-cheese pizza, bake it, plate it, then add fresh onion and deliver.",

"subgoals": \[{"id": "sg1\_retrieve\_dough", "text": "Agent retrieves dough.",

"rewards": \[{"id": "sg1\_approach\_dough", "type": "shaping", "once": false, "amount": 1, "condition": "agent\_distance\_to\_static\_tile(item\_type\=17,map\_tile\=17)<2.0"},

{"id": "sg1\_pickup\_dough", "type": "event", "once": true, "amount": 15, "condition": "exists\_item(type\=17,container\_id\==agent\_id,consumed\==0)"}\]},

{"id": "sg2\_place\_dough\_on\_counter", "text": "Place dough on counter.", "depends\_on": \["sg1\_pickup\_dough"\],

"rewards": \[{"id": "sg2\_place\_dough", "type": "event", "once": true, "amount": 20, "condition": "exists\_item(type\=17,container\_is\_counter\==true,consumed\==0)"}\]},

{"id": "sg3\_prepare\_tomato", "text": "Fetch and chop tomato.",

"rewards": \[{"id": "sg3\_approach\_tomato", "type": "shaping", "once": false, "amount": 1, "condition": "agent\_distance\_to\_static\_tile(item\_type\=3,map\_tile\=3)<2.0"},

{"id": "sg3\_pickup\_tomato", "type": "event", "once": true, "amount": 10, "condition": "exists\_item(type\=3,container\_id\==agent\_id,consumed\==0)"},

{"id": "sg3\_tomato\_on\_knife", "type": "event", "once": true, "amount": 10, "condition": "exists\_item(type\=3,container\_is\_knife\==true,consumed\==0)"},

{"id": "sg3\_chopped\_tomato\_done", "type": "event", "once": true, "amount": 20, "condition": "exists\_item(type\=3,is\_chopped\==true,consumed\==0)"}\]},

{"id": "sg4\_assemble\_raw\_tomato\_pizza", "text": "Assemble raw tomato\-cheese pizza.", "depends\_on": \["sg2\_place\_dough\_on\_counter", "sg3\_chopped\_tomato\_done"\],

"rewards": \[{"id": "sg4\_add\_tomato", "type": "event", "once": true, "amount": 15, "condition": "exists\_composite\_item(kind\=’dough+tomato’,on\_counter\=true,consumed\==0)"},

{"id": "sg4\_add\_cheese", "type": "event", "once": true, "amount": 15, "condition": "exists\_composite\_item(kind\=’dough+tomato+cheese’,on\_counter\=true,

consumed\==0)"},

{"id": "sg4\_raw\_pizza\_ready", "type": "event", "once": true, "amount": 20, "condition": "exists\_item(type\=’raw\_tomato\_pizza’,on\_counter\=true,consumed\==0)"}\]},

{"id": "sg5\_bake\_pizza", "text": "Bake pizza to completion.", "depends\_on": \["sg4\_raw\_pizza\_ready"\],

"rewards": \[{"id": "sg5\_into\_oven", "type": "event", "once": true, "amount": 20, "condition": "exists\_item(type\=’raw\_tomato\_pizza’,container\_is\_oven\==true,consumed\==0)"},

{"id": "sg5\_bake\_progress", "type": "shaping", "once": false, "amount": 2, "condition": "exists\_item(type\=’raw\_tomato\_pizza’,container\_is\_oven\==true,

cook\_progress\_increased\==true)"},

{"id": "sg5\_baked\_done", "type": "event", "once": true, "amount": 25, "condition": "exists\_item(type\=20,container\_is\_oven\==true OR on\_counter\==true,is\_burned\==false,consumed\==0)"}\]},

{"id": "sg6\_plate\_baked\_pizza", "text": "Plate the baked pizza.", "depends\_on": \["sg5\_baked\_done"\],

"rewards": \[{"id": "sg6\_empty\_plate", "type": "event", "once": true, "amount": 10, "condition": "exists\_item(type\=5,on\_counter\=true,is\_empty\==true,consumed\==0)"},

{"id": "sg6\_pizza\_on\_plate", "type": "event", "once": true, "amount": 25, "condition": "exists\_item(type\=20,container\_is\_plate\==true,consumed\==0)"}\]},

{"id": "sg7\_add\_onion\_topping", "text": "Chop onion and add to plated pizza.", "depends\_on": \["sg6\_pizza\_on\_plate"\],

"rewards": \[{"id": "sg7\_pickup\_onion", "type": "event", "once": true, "amount": 10, "condition": "exists\_item(type\=8,container\_id\==agent\_id,consumed\==0)"},

{"id": "sg7\_onion\_on\_knife", "type": "event", "once": true, "amount": 10, "condition": "exists\_item(type\=8,container\_is\_knife\==true,consumed\==0)"},

{"id": "sg7\_chopped\_onion", "type": "event", "once": true, "amount": 15, "condition": "exists\_item(type\=8,is\_chopped\==true,consumed\==0)"},

{"id": "sg7\_onion\_added", "type": "event", "once": true, "amount": 30, "condition": "exists\_composite\_item(kind\=’pizza\_onion’,container\_is\_plate\==true,

consumed\==0)"}\]},

{"id": "sg8\_deliver\_onion\_pizza", "text": "Deliver final onion pizza.", "depends\_on": \["sg7\_onion\_added"\],

"rewards": \[{"id": "sg8\_approach\_delivery", "type": "shaping", "once": false, "amount": 2, "condition": "agent\_distance\_to\_tile\_with\_value(7)<2.0"},

{"id": "sg8\_deliver\_success", "type": "terminal", "once": true, "amount": 200, "condition": "exists\_composite\_item(kind\=’pizza\_onion’,container\_is\_delivery\==true,

consumed\==0)"}\]}\]}

Listing 5: Example Output of Semantic Reward Rules (Stage 3).

{"task\_id": "Quest\_Onion\_Pizza\_Update",

"subgoals": \[{"index": 2, "text": "Assemble raw pizza with dough, chopped tomato, and cheese.",

"locations": \[{"file": "overcooked/overcookedPlus/items.py", "span": \[737, 765\], "kind": "function", "change\_type": "modified", "symbol": "try\_synthesis", "qualname": "Plate.try\_synthesis"},

{"file": "overcooked/overcookedPlus/items.py", "span": \[778, 812\], "kind": "function", "change\_type": "modified", "symbol": "contain", "qualname": "Plate.contain"},

{"file": "overcooked/overcookedPlus/items.py", "span": \[981, 989\], "kind": "variable", "change\_type": "modified", "symbol": "synthesis\_table", "qualname": "synthesis\_table"}\]},

{"index": 3, "text": "Bake the raw pizza in the oven until it is cooked but not burned.",

"locations": \[{"file": "overcooked/overcookedPlus/items.py", "span": \[607, 627\], "kind": "function", "change\_type": "modified", "symbol": "cook", "qualname": "Oven.cook"},

{"file": "overcooked/overcookedPlus/module/event\_manager.py", "span": \[568, 590\], "kind": "function", "change\_type": "modified", "symbol": "\_collect\_auto", "qualname": "EventManager.\_collect\_auto"},

{"file": "overcooked/overcookedPlus/module/event\_manager.py", "span": \[455, 483\], "kind": "function", "change\_type": "modified", "symbol": "\_do\_pickup\_into\_plate",

"qualname": "EventManager.\_do\_pickup\_into\_plate"}\]},

{"index": 5, "text": "Fetch an onion, chop it on the knife, and add it onto the plated pizza as an extra topping.",

"locations": \[{"file": "overcooked/overcookedPlus/items.py", "span": \[261, 272\], "kind": "class", "change\_type": "added", "symbol": "Onion", "qualname": "Onion"},

{"file": "overcooked/overcookedPlus/items.py", "span": \[515, 541\], "kind": "function", "change\_type": "modified", "symbol": "chop", "qualname": "Knife.chop"},

{"file": "overcooked/overcookedPlus/module/event\_manager.py", "span": \[232, 251\], "kind": "function", "change\_type": "modified", "symbol": "\_do\_usage", "qualname": "EventManager.\_do\_usage"},

{"file": "overcooked/overcookedPlus/items.py", "span": \[778, 812\], "kind": "function", "change\_type": "modified", "symbol": "contain", "qualname": "Plate.contain"}\]}\]}

Listing 6: Example Output of mapped Structural Anchors (Stage 4).

Craft\_Gold\_Axe, Craft\_Gold\_Boots, Craft\_Gold\_Chestplate, Craft\_Gold\_Helmet, Craft\_Gold\_Leggings, Craft\_Gold\_Pickaxe, Craft\_Gold\_Shovel, Craft\_Gold\_Sword, Kill\_Chicken\_With\_Gold\_Sword, Kill\_Creeper\_With\_Gold\_Sword, Kill\_Skeleton\_With\_Gold\_Sword, Kill\_Slime\_With\_Gold\_Sword, Kill\_Spider\_With\_Gold\_Sword, Kill\_Zombie\_With\_Gold\_Sword, Mine\_Gold\_Ore, Craft\_Gold\_Shield, Craft\_Gold\_Hoe, Mine\_Gold\_Nugget, Smelt\_Gold\_Ingot

Listing 7: List of newly added tasks used in Minecraft.

Pizza, Pizza Lettuce, Pizza Onion, Pizza Steak, Pizza Fish, Pizza Rice, Roastfish, Roastfish Tomato, Roastfish Steak, Roastfish Rice, Roastfish Cheese, Onion Dough, Rice Dough, Pizza Tomato Cheese, Roastfish Onion, Roastfish Lettuce, Dough, Tomato Dough, Lettuce Dough, Cheese Dough, Tomato Steak Fish Dough,

Listing 8: List of newly added tasks used in Overcooked.

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Data availability

Data will be made available on request.

## References

-   \\bibcommenthead
-   Newzoo \[2024\] Newzoo: Newzoo’s Global Games Market Report 2024 - Free Version. Accessed: 2025-10-29 (2024). [https://newzoo.com/resources/trend-reports/newzoos-global-games-market-report-2024-free-version](https://newzoo.com/resources/trend-reports/newzoos-global-games-market-report-2024-free-version)
-   Wu et al. \[2020\] Wu, Y., Chen, Y., Xie, X., Yu, B., Fan, C., Ma, L.: Regression testing of massively multiplayer online role-playing games. In: 2020 IEEE International Conference on Software Maintenance and Evolution (ICSME), pp. 692–696 (2020). [https://doi.org/10.1109/ICSME46990.2020.00074](https://doi.org/10.1109/ICSME46990.2020.00074)
-   Politowski et al. \[2016\] Politowski, C., Fontoura, L., Petrillo, F., Guéhéneuc, Y.-G.: Are the old days gone? a survey on actual software engineering processes in video game industry. In: Proceedings of the 5th International Workshop on Games and Software Engineering. GAS ’16, pp. 22–28. Association for Computing Machinery, New York, NY, USA (2016). [https://doi.org/10.1145/2896958.2896960](https://doi.org/10.1145/2896958.2896960) . [https://doi.org/10.1145/2896958.2896960](https://doi.org/10.1145/2896958.2896960)
-   Aho et al. \[2006\] Aho, A.V., Lam, M.S., Sethi, R., Ullman, J.D.: Compilers: Principles, Techniques, and Tools (2nd Edition). Addison Wesley, ??? (2006)
-   Baxter et al. \[1998\] Baxter, I.D., Yahin, A., Moura, L., Sant’Anna, M., Bier, L.: Clone detection using abstract syntax trees. In: Proceedings. International Conference on Software Maintenance (Cat. No. 98CB36272), pp. 368–377 (1998). [https://doi.org/10.1109/ICSM.1998.738528](https://doi.org/10.1109/ICSM.1998.738528)
-   Livshits and Lam \[2005\] Livshits, V.B., Lam, M.S.: Finding security vulnerabilities in java applications with static analysis. In: Proceedings of the 14th Conference on USENIX Security Symposium - Volume 14. SSYM’05, p. 18. USENIX Association, USA (2005)
-   Sutton and Barto \[2018\] Sutton, R.S., Barto, A.G.: Reinforcement Learning: An Introduction. MIT press, ??? (2018)
-   Mnih et al. \[2015\] Mnih, V., Kavukcuoglu, K., Silver, D., Rusu, A.A., Veness, J., Bellemare, M.G., Graves, A., Riedmiller, M., Fidjeland, A.K., Ostrovski, G., et al.: Human-level control through deep reinforcement learning. nature 518(7540), 529–533 (2015)
-   Schulman et al. \[2017\] Schulman, J., Wolski, F., Dhariwal, P., Radford, A., Klimov, O.: Proximal Policy Optimization Algorithms (2017). [https://arxiv.org/abs/1707.06347](https://arxiv.org/abs/1707.06347)
-   Pathak et al. \[2017\] Pathak, D., Agrawal, P., Efros, A.A., Darrell, T.: Curiosity-driven exploration by self-supervised prediction. In: Proceedings of the 34th International Conference on Machine Learning - Volume 70. ICML’17, pp. 2778–2787. JMLR.org, ??? (2017)
-   Ghost Town Games \[2016\] Ghost Town Games: Overcooked. [https://www.ghosttowngames.com/overcooked](https://www.ghosttowngames.com/overcooked). Game developed by Ghost Town Games and published by Team17 (2016)
-   Mojang Studios \[2009\] Mojang Studios: Minecraft. [https://www.minecraft.net](https://www.minecraft.net/). Sandbox video game developed by Mojang Studios (2009)
-   Cai et al. \[2024\] Cai, J., Li, J., Li, N., Zhang, M., Yang, R., Tei, K.: Overcooked plus: A comprehensive cooking scenario testbed for enhancing the evaluation of autonomous planning algorithms. In: 2024 IEEE International Conference on Autonomic Computing and Self-Organizing Systems Companion (ACSOS-C), pp. 146–151 (2024). IEEE
-   Hu et al. \[2024\] Hu, J., Zhang, M., Liu, B., Wu, Y., Chen, Y.: A language-guided acceleration method for smoke testing of game quests. In: 2024 IEEE 35th International Symposium on Software Reliability Engineering Workshops (ISSREW), pp. 7–12 (2024). [https://doi.org/%\*\*\*\*␣0\_Main.bbl␣Line␣250␣\*\*\*\*10.1109/ISSREW63542.2024.00039](https://doi.org/%****%200_Main.bbl%20Line%20250%20****10.1109/ISSREW63542.2024.00039)
-   Schulman et al. \[2017\] Schulman, J., Wolski, F., Dhariwal, P., Radford, A., Klimov, O.: Proximal policy optimization algorithms. arXiv preprint arXiv:1707.06347 (2017)
-   Raffin et al. \[2021\] Raffin, A., Hill, A., Gleave, A., Kanervisto, A., Ernestus, M., Dormann, N.: Stable-baselines3: Reliable reinforcement learning implementations. Journal of machine learning research 22(268), 1–8 (2021)
-   Ostrowski and Aroudj \[2013\] Ostrowski, M., Aroudj, S.: Automated regression testing within video game development. GSTF Journal on Computing (JoC) 3(2), 10 (2013) [https://doi.org/10.7603/s40601-013-0010-4](https://doi.org/10.7603/s40601-013-0010-4)
-   Mioto and Petrillo \[2025\] Mioto, V., Petrillo, F.: A mapping of recording-based game test automation tools. In: 2025 IEEE/ACM 9th International Workshop on Games and Software Engineering (GAS), pp. 1–8 (2025). [https://doi.org/10.1109/GAS66647.2025.00006](https://doi.org/10.1109/GAS66647.2025.00006)
-   Spronck et al. \[2006\] Spronck, P., Ponsen, M., Sprinkhuizen-Kuyper, I., Postma, E.: Adaptive game ai with dynamic scripting. Machine Learning 63(3), 217–248 (2006) [https://doi.org/10.1007/s10994-006-6205-6](https://doi.org/10.1007/s10994-006-6205-6)
-   Cho et al. \[2010\] Cho, C.-S., Lee, D.-C., Sohn, K.-M., Park, C.-J., Kang, J.-H.: Scenario-based approach for blackbox load testing of online game servers. In: 2010 International Conference on Cyber-Enabled Distributed Computing and Knowledge Discovery, pp. 259–265 (2010). [https://doi.org/10.1109/CyberC.2010.54](https://doi.org/10.1109/CyberC.2010.54)
-   iXie Gaming \[2024\] iXie Gaming: A Comprehensive Review of Game Test Automation Tools. Accessed: 2025-10-14 (2024). [https://www.ixiegaming.com/blog/comprehensive-review-game-test-automation-tools/](https://www.ixiegaming.com/blog/comprehensive-review-game-test-automation-tools/)
-   Rothermel and Harrold \[1996\] Rothermel, G., Harrold, M.J.: A safe, efficient regression test selection technique. ACM Transactions on Software Engineering and Methodology (TOSEM) 6(2), 173–210 (1996)
-   Yu et al. \[2023\] Yu, J., Wu, Y., Xie, X., Le, W., Ma, L., Chen, Y., Hu, J., Zhang, F.: Gamerts: A regression testing framework for video games. In: 2023 IEEE/ACM 45th International Conference on Software Engineering (ICSE), pp. 1393–1404 (2023). [https://doi.org/10.1109/ICSE48619.2023.00122](https://doi.org/10.1109/ICSE48619.2023.00122)
-   Iftikhar et al. \[2015\] Iftikhar, S., Iqbal, M.Z., Khan, M.U., Mahmood, W.: An automated model based testing approach for platform games. In: 2015 ACM/IEEE 18th International Conference on Model Driven Engineering Languages and Systems (MODELS), pp. 426–435 (2015). [https://doi.org/10.1109/MODELS.2015.7338274](https://doi.org/10.1109/MODELS.2015.7338274)
-   Hernández Bécares et al. \[2017\] Hernández Bécares, J., Costero Valero, L., Gómez Martín, P.P.: An approach to automated videogame beta testing. Entertainment Computing 18, 79–92 (2017) [https://doi.org/10.1016/j.entcom.2016.08.002](https://doi.org/10.1016/j.entcom.2016.08.002)
-   Stahlke et al. \[2020\] Stahlke, S., Nova, A., Mirza-Babaei, P.: Artificial players in the design process: Developing an automated testing tool for game level and world design. In: Proceedings of the Annual Symposium on Computer-Human Interaction in Play. CHI PLAY ’20, pp. 267–280. Association for Computing Machinery, New York, NY, USA (2020). [https://doi.org/10.1145/3410404.3414249](https://doi.org/10.1145/3410404.3414249) . [https://doi.org/10.1145/3410404.3414249](https://doi.org/10.1145/3410404.3414249)
-   Stahlke et al. \[2019\] Stahlke, S.., Nova, A., Mirza-Babaei, P.: Artificial playfulness: A tool for automated agent-based playtesting. In: Extended Abstracts of the 2019 CHI Conference on Human Factors in Computing Systems. CHI EA ’19, pp. 1–6. Association for Computing Machinery, New York, NY, USA (2019). [https://doi.org/10.1145/3290607.3313039](https://doi.org/10.1145/3290607.3313039)
-   Bergdahl et al. \[2020\] Bergdahl, J., Gordillo, C., Tollmar, K., Gisslén, L.: Augmenting automated game testing with deep reinforcement learning. In: 2020 IEEE Conference on Games (CoG), pp. 600–603 (2020). [https://doi.org/10.1109/CoG47356.2020.9231552](https://doi.org/10.1109/CoG47356.2020.9231552)
-   Gordillo et al. \[2021\] Gordillo, C., Bergdahl, J., Tollmar, K., Gisslén, L.: Improving playtesting coverage via curiosity driven reinforcement learning agents. In: 2021 IEEE Conference on Games (CoG), pp. 1–8 (2021). [https://doi.org/10.1109/CoG52621.2021.9619048](https://doi.org/10.1109/CoG52621.2021.9619048)
-   Zheng et al. \[2019\] Zheng, Y., Xie, X., Su, T., Ma, L., Hao, J., Meng, Z., Liu, Y., Shen, R., Chen, Y., Fan, C.: Wuji: Automatic online combat game testing using evolutionary deep reinforcement learning. In: 2019 34th IEEE/ACM International Conference on Automated Software Engineering (ASE), pp. 772–784 (2019). [https://doi.org/10.1109/ASE.2019.00077](https://doi.org/10.1109/ASE.2019.00077)
-   Holmgård et al. \[2019\] Holmgård, C., Green, M.C., Liapis, A., Togelius, J.: Automated playtesting with procedural personas through mcts with evolved heuristics. IEEE Transactions on Games 11(4), 352–362 (2019) [https://doi.org/10.1109/TG.2018.2808198](https://doi.org/10.1109/TG.2018.2808198)
-   Ariyurek et al. \[2023\] Ariyurek, S., Surer, E., Betin-Can, A.: Playtesting: What is beyond personas. IEEE Transactions on Games 15(3), 348–359 (2023) [https://doi.org/10.1109/TG.2022.3165882](https://doi.org/10.1109/TG.2022.3165882)
-   Ariyurek et al. \[2021\] Ariyurek, S., Betin-Can, A., Surer, E.: Automated video game testing using synthetic and humanlike agents. IEEE Transactions on Games 13(1), 50–67 (2021) [https://doi.org/10.1109/TG.2019.2947597](https://doi.org/10.1109/TG.2019.2947597)
-   Mu et al. \[2025\] Mu, E., Cai, J., Lu, Y., Zhang, M., Tei, K., Li, J.: Knowledge Graph-enhanced Large Language Model for Incremental Game PlayTesting (2025). [https://arxiv.org/abs/2511.02534](https://arxiv.org/abs/2511.02534)
-   Paduraru and Stefanescu \[2024\] Paduraru, C., Stefanescu, S.: Unit test generation using large language models for unity games. IEEE Transactions on Games (2024)
-   Taesiri et al. \[2022\] Taesiri, M.R., Macklon, F., Wang, Y., Shen, H., Bezemer, C.-P.: Large language models are pretty good zero-shot video game bug detectors. arXiv preprint arXiv:2210.02506 (2022)
-   Xu et al. \[2024\] Xu, J., Li, J., Liu, Z., Suryanarayanan, N.A.V., Zhou, G., Guo, J., Iba, H., Tei, K.: Large Language Models Synergize with Automated Machine Learning (2024)
