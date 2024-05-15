# The Cost of Representation by Subset Repairs
This is the github repository for paper "The Cost of Representation by Subset Repairs". This version is only for the reviewers.

## Project Structure
+ `data/`: a folder containing the input datas (input relations, FD sets, RCs). There are two examples for a demo below stored in `data/example/` and `data/example2/` respectively. There are also our input datas for the experiments in `data/input_data_acs/` and `data/input_data_compas/` (detailed explanation below).
+ `src/`: a folder containing the source codes
+ `result/`: a folder containing the results of the two examples stored in `result/example/` and `result/example2` respectively
+ `.gitignore`
+ `README.md`
+ `requirements.txt`: python packages' requirements (package and version)
<!-- + `data_generator/`: a folder containing the generator codes utilized to obtain inputs for our experiments (for different public datasets, for different noise level, for different input relation size, for different FD sets, etc.) -->
+ `The_Cost_of_Representation_by_Subset_Repairs_full_version.pdf`: the full version of our paper

<!-- Note that we only show parts of the inputs for our experiments (smaller ones, i.e., 4K-10K). The large-scale inputs are too large to put on a github repository. The datasets we used are public and the codes for generating inputs are in `data_generator/`. -->

## Python Package Requirement
```
gurobipy==10.0.3
networkx==3.1
numpy==1.24.3
pandas==1.5.3
scipy==1.10.1
tqdm==4.65.0
```
gurobipy is the [python version](https://pypi.org/project/gurobipy/) of Gurobi Optimizer utilized for solving (I)LPs in this project. To solve large-scale (even a few Ks rows in our inputs) (I)LP, the users will need a full license. We utilize the Gurobi Academic Licence ([details](https://www.gurobi.com/academia/academic-program-and-licenses/) here).

networkx is utlized for vertex cover problem.

## Example Usages
With all the packages ready (including Gurobi licence), onc can run our codes with this instruction.
```
cd src
python3 driver.py --help
```
You should see the usage as follow:
```
usage: driver.py [-h] [--input_dir INPUT_DIR] [--result_dir RESULT_DIR] [--relation RELATION] [--fdset FDSET] [--rc RC]
                 [--solvers SOLVERS] [--report_violation] [--seed SEED]

options:
  -h, --help            show this help message and exit
  --input_dir INPUT_DIR
                        the (related) input directory
  --result_dir RESULT_DIR
                        the (related) output directory
  --relation RELATION   the filename of input relation
  --fdset FDSET         the filename of fdset
  --rc RC               the filename of RC
  --solvers SOLVERS     comma-separated list of solvers,
                        [lhschain_dp,globalilp,lp_greedyrounding,lp_reprrounding,fdcleanser,dp_baseline,vc_approx_baseline,ilp_baseline]
  --report_violation    (Optional) report the violations (in terms of FDs) of the tuples retained by the RS-repair
  --seed SEED           (Optional) the random seed
```
Note that the name of algorithm matches what we showed in our paper.
### Example 1: A sample of ACS, 500 rows, 10% noise, non-chain FD set, RC on NATIVITY
For this case, we run these algorithms: globalilp, lp_greedyrounding, lp_reprrounding, fdcleaner, vc_approx_baseline, ilp_baseline
```
python3 driver.py --input_dir ../data/example/ --result_dir ../result/example/ --relation example_relation.csv --fdset example_fdset.txt --rc example_rc.txt --solvers globalilp,lp_greedyrounding,lp_reprrounding,fdcleanser,vc_approx_baseline,ilp_baseline
```
There will be 3 parts of outputs. The first part is the output in terminal:
```
Working on solver: globalilp
Set parameter WLSAccessID
Set parameter WLSSecret
Set parameter LicenseID to value 2421665
Academic license 2421665 - for non-commercial use only - registered to yu___@duke.edu
Set parameter Threads to value 30
Set parameter Seed to value 42
[0.273s] Size of RS-repair(globalilp): 290
Finished!
Working on solver: lp_greedyrounding
Set parameter Seed to value 42
[0.38s] Size of RS-repair(lp_greedyrounding): 285
Finished!
Working on solver: lp_reprrounding
Set parameter Seed to value 42
[0.564s] Size of RS-repair(lp_reprrounding): 280
Finished!
Working on solver: fdcleanser
[1.172s] Size of RS-repair(fdcleanser): 275
Finished!
Working on solver: vc_approx_baseline
[0.112s] Size of RS-repair(vc_approx_baseline): 30
Finished!
Working on solver: ilp_baseline
Set parameter Threads to value 30
Set parameter Seed to value 42
Start Optimization
[0.22s] Size of RS-repair(ilp_baseline): 245
Finished!
```
Each solver we tried will start with a "Working on solver:xxx" and end with a "Finished". There will be a line in the middle shows the runtime and the sizes (or the numbers of retained tuples) of RS-repair.

Something special about the output of `globalilp` is related to Gurobi. There will be some output from Gurobi, including the license ID, parameters, etc.. This information will be printed out the first time we start the engine of Gurobi Optimizer. Since `globalip` is the first solver we try in this command, this info. is therefore attached to the output of `globalilp`

The second and third parts of the output are put in `result/example/` (or `../result/example/` related to where the driver locates)
```
### In result/example/, there are
[before-postclean]ilp_baseline.txt
[before-postclean]vc_approx_baseline.txt
fdcleanser.txt
globalilp.txt
ilp_baseline.txt
lp_greedyrounding.txt
lp_reprrounding.txt
vc_approx_baseline.txt
```
For non-baseline algorithms (`fdcleaner`,`lp_greedyrounding`,`lp_reprrounding`,`globalilp`), there is one output file for each of them; for baseline algorithms (`ilp_baseline`, `vc_approx_baseline`), there are two output files for each of them, because we also store the information about the S-repair before post-cleaning. These files look similar. For example, let's take a look of the first few lines of `globalilp.txt`:
```
Overall Time cost(in secs.): 0.27319931983947754
Size of S-repair: 290
Distribution of Representative Column : {'2': 58, '1': 232}
Time cost of PostClean(in secs.): 0.007347583770751953
RAC1P SEX REGION ST CIT  NATIVITY DIS DIVISION RAC2P POBP WAOB    ID
    8   2      9 72   4         2   2        6    67  327    3 32684
    6   2      2 18   4         2   2        3    41  205    4 11741
    8   1      4  6   4         2   2        9    67  303    3  3069
    6   2      4  6   4         2   2        9    42  206    4  1836
    1   2      3 40   4         2   2        7     1  303    3 23626
    9   1      3 48   5         2   2        7    68  303    3 28724
    6   2      4  6   5         2   2        9    47  211    4  4866
    6   2      1 25   5         2   2        1    38  210    4 14390
    8   1      3 48   5         2   2        7    67  303    3 27727
    9   1      4 32   5         2   2        8    68  303    3 17705
    6   2      3 24   4         2   2        5    49  217    4 14013
...
```
The first line is the overall time cost for `globalilp` and the second line is the size of RS-repair. The third row is the distribution of the representation column (or the sensitive attribute in the paper). In this case, there are 58 tuples with sensitive value 2 and 232 tuples with sensitive value 1. The fourth row is the runtime of PostClean. The rest of the output is the RS-repair in the form of a readable `pandas.Dataframe` string.
### Example 2: A sample of ACS, 500 rows, 10% noise, chain FD set, RC on NATIVITY
For this case, we run these algorithms: globalilp, lhschain_dp, dp_baseline, vc_approx_baseline, ilp_baseline. Here is the command:
```
python3 driver.py --input_dir ../data/example2/ --result_dir ../result/example2/ --relation example2_relation.csv --fdset example2_fdset.txt --rc example2_rc.txt --solvers globalilp,lhschain_dp,dp_baseline,ilp_baseline,vc_approx_baseline
```
The explanations are omitted in this example and here is the output in terminal:
```
Working on solver: globalilp
Set parameter WLSAccessID
Set parameter WLSSecret
Set parameter LicenseID to value 2421665
Academic license 2421665 - for non-commercial use only - registered to yu___@duke.edu
Set parameter Threads to value 30
Set parameter Seed to value 42
[0.516s] Size of RS-repair(globalilp): 315
Finished!
Working on solver: lhschain_dp
[1.46s] Size of RS-repair(lhschain_dp): 315
Finished!
Working on solver: dp_baseline
[0.468s] Size of RS-repair(dp_baseline): 265
Finished!
Working on solver: ilp_baseline
Set parameter Threads to value 30
Set parameter Seed to value 42
Start Optimization
[0.185s] Size of RS-repair(ilp_baseline): 250
Finished!
Working on solver: vc_approx_baseline
[0.544s] Size of RS-repair(vc_approx_baseline): 265
Finished!
```
The other outputs are in `result/example2/` (or relatively `../result/example2/`).

## Format of Input
The input consists of three files (one for the relation, one for the FD set, one for the RC). We specify the format of input through the example we mentioned above.
### Relation
Take the `data/example/example_relation.csv` as an example:
```
RAC1P,SEX,REGION,ST,CIT,NATIVITY,DIS,DIVISION,RAC2P,POBP,WAOB,ID
1,2,2,42,5,2,2,2,1,301,7,24880
6,2,4,33,4,2,2,0,45,233,4,17891
8,2,9,72,4,2,2,6,67,327,3,32684
3,1,9,42,5,2,2,9,27,313,3,3847
6,2,2,18,4,2,2,3,41,205,4,11741
8,1,4,6,4,2,2,9,67,303,3,3069
6,2,4,6,4,2,2,9,42,206,4,1836
1,1,1,34,4,2,2,3,1,110,5,18902
1,2,3,40,4,2,2,7,1,303,3,23626
9,1,3,48,5,2,2,7,68,303,3,28724
...
```
There is a header as usual in csv files and the delimeter is comma by default. We expect the input relation does not have NAN values, but there is a `dropna` option (set as False by default) in `Class Table`.
### FDSet
Take the `data/example/example_fdset.txt` as an example:
```
CIT -> NATIVITY
ST -> DIVISION
DIVISION -> REGION
RAC2P -> RAC1P
POBP -> WAOB
```
Each line is a FD and the LHS and RHS are splitted by "->". The LHS (and respectively RHS) firstly call `.strip()` to clean the leading/ending whitespaces. The LHS (and respectively RHS) can be either a single column or a comma-separated list of columns. If a RHS is more than one column, the corresponding FD will be splitted into multiple FDs, where each of them has a dinstinct singleton RHS.
### RC
Take the `data/example/example_rc.txt` as an example:
```
NATIVITY
1,2
4/5,1/5
```
The first line is the name of the sensitive attribute/column. The second line is a comma-separted list of sensitive values. The third line, corresponding to each sensitive value in the second line, is a comma-separated list of lower-bound proportions that are expressed by fractional numbers. A fractional number is in the form of "X/Y" where both X and Y are integers.

## Experiment Input Data
They are in `/data/input_data_acs/` (resp. `/data/input_data_compas/`). Under these two directories, there are two folders `chain_FD/` and `non_chain_FD/`, correpsonding to the inputs of each type of FD set (chain and non-chain). Under these folders, you should see three types of files:
+ `SIZE_errrate_dirty.csv`: the input relation to repair. SIZE will be the size of the input relation (e.g. 4000). errrate is a fractional number (e.g. 0.1).
+ `chain_fdset.txt` or `non_chain_fdset.txt`: the FD set.
+ `ATTRIBUTE_rc.txt`: the RC. ATTRIBUTE will be the name of the sensitive attribute (e.g. SEX).

## Code Workflow
Here is the list of codes in `src/`
```
$ ls src/ approx.py
./
../
approx.py
color_distribution.py
compute_error.py
driver.py
exact.py
functional_dependency.py
matching.py
postclean.py
reduction.py
table.py
utility.py
vertex_cover_approx.py
```
`driver.py` is the beginning of everything, where we load the relation, the FD set, and the RC. Next,
+ we build a relation through the `Class Table` implemented in `table.py`;
+ we parse the FD set through the `Class FDSet` implemented in `functional_dependency.py`;
+ we parse the RC through the `Class RepresentationConstraint` implemented in `representation_constraint.py`.

Beside this, each table is associated with a `Class ColorDistribution` implemented in `color_distribution.py` that is utilied to keep track of the distribution of the sensitive column.

Then, `driver.py` calls `solve()` the problem instance by each solver. And it distributes the workflow to `exact.py`, `reduction.py`, and `approx.py` according to what the solver is.

In `exact.py`, we implemented `globalilp`, `ilp_baseline` through Gurobi.

In `approx.py`, we implemented LP relaxations and roundings.

In `reduction.py`, we implemented `lhschain_dp`, `dp_baseline`, `lp_greedyrounding`, `lp_reprrounding`, `fdcleanser`, `vc_approx_baseline`. The reason that the last 4 heuristics/approximations are here is they all firstly apply reduction exhaustively.

After getting the candidate set from out algorithms or a S-repair from the baseline algorithms, `driver.py` will call PostClean implemented in `postclean.py`.

`compute_error.py`, `utility.py`, and `vertex_cover_approx.py` are a collection of some helper functions. `matching.py` is not really utilized in our experiments, but has some old greedy ideas to make an attempt in LHS marriages.
