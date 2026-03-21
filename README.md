# BYU's CE 321 Project 3 Grader

The purpose of this project is to help you gain familiarity with the analysis of wind loads and indeterminate structures and to see, through experience, the consequences of introducing indeterminacy into a truss.
You will then work to optimize the selected truss based on two separate LRFD load scenarios.

A prompt has been provided to you on Learning Suite indicating the questions that you are to address.
This repository will allow you to test the software that you have developed to determine if your code functions properly.
It will also allow you to estimate your final score for the project based on updates that you make to the `project_3_submission.txt` file.
As with other projects, this file must be uploaded to receive full credit for this assignment.

## Instructions

Navigate to this repository, sign into your GitHub account, and then create a private repository using this repository as a template.
(Particularly, do not make your repository public, and do not fork this repository.)
After you have done this, navigate to your copy of this repository on your GitHub account.

Update `project_3_submission.txt` based on the set of questions described in the prompt provided on Learning Suite.
You will also need to update the `Solver_Trusses.py` file based on the code that you develop in Task 2 of the project.
You may update your `Main_Trusses.py` file here, but if you do so, be sure that it loads a file that you can access, such as `Gabled_Howe_6_Panel.csv` or else your software may break the grader. 
You should not need to change or update any other Python files.

For full credit, you will also need to input 8 CSV files in the `csvs` folder based on structural analyses for simply supported, two pins, and three pins with and without wind loads, as well as a single optimized structure (with and without wind).
Please see the names that are requested from our project prompt.
Do not delete the Default file in the CSV folder because it is used to help with grading.
Your files should include appropriate loads, constraints, optimization, etc as outlined in the project prompt.

## Evaluation

Every time you update a file here, it the testing suite will check everything that you uploaded.
To check this, please navigate to the top of this webpage and click on the "Actions" button.
Here, you will see workflow runs.
The most recent updates that you made will be in the top workflow run.
If you see a green checkmark, this means that your coding portion of the software passed all tests.
If not, the coding portion did not pass the online checking system.

Click on the topmost of these runs.
Then click on "build."
You will then see a dropdown of activities that are being run or have been run for this submission.
The "Test Solver Software" runs some tests to see if your methods to compute axial forces, normal stresses, and maximal buckling loads appear to give correct results.
If yes, you will see this complete with a green checkmark.
Otherwise, it will give a red X and you can click on it to see which test failed.
Finally, an estimate of your final grade for Project 4 will be given in the "Grade Project 4 Submission" dropdown tab, where you will see if your submitted answers are correct or not.
Unlike other grading systems for previous projects, only the partial credit option works here (meaning that you can only be evaluated based on the accumulation of your previous answers, as opposed to a more simple grading scheme where we only check numbers against the correct answer but not against potential previous errors that are then used correctly).
If you have questions about this, please reach out to Dr. Shepherd.
