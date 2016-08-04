# Workflow for Framework Documents:
1) Teams work together to develop ICD Framework documents, which are Word documents that describe the basic agreements on the ICD. These are used to guide the detailed APIs and ICD documents that are developed using Model Files and the ICD Database.
2) ICD Framework Documents are published to Docushare following the standard systems engineering process for releasing ICD documents (Reference Document Approval Matrix and Configuration Control Plan).

# Workflow for detailed APIs and ICDs using the ICD Database (Assume Framework document is published already)

# Overview:
The GitHub model file repository (See https://github.com/tmtsoftware/ICD-Model-Files) is structured to have a Submodule for each SubSystem (IRIS-Model-Files, TCS-Model-Files, etc) as well as a Root Repository that references specific commits to these submodules.  Individual teams can push changes to their Submodules without external review or approval. The approval / release process involves the step of updating the commit to the Root Repository. This is done at the time of a formal release of an API.  ICDs are generated from the API commits that are in the Root Repository.  All ICDs related to an updated API are re-published when that API is approved into the Root Repository.  Several APIs will often be considered together for approval / release of new ICDs.

# Workflow Steps:
1) Teams work with each other to agree ICDs, updating their API’s as needed to reach agreement. During this process, each team updates their API’s by pushing to their GitHub submodule, for example “IRIS-Model-Files”.  No approval is required for this step.
2) When ready, the teams request Systems Engineering to release new version(s) of API(s) and ICD(s).
3) SE Reviews the request, consults with stakeholders and agrees/disagrees to publishing the ICD.
4) Once approved, TMT systems engineering updates the Root Repository to include the changes made in each submodule repository.  One this is complete the updated APIs and ICDs can be loaded into the ICD Database using the ingest.sh script.
5) TMT Systems Engineering publishes the ICD(s) related to updated Root Repository APIs in .pdf format on Docushare.  This and the accompanying Framework document form the full ICD.

# To Do:
- Set up permissions so that each team can push to their own repository
- Set up permissions so that Scott can merge the pull request.
- Set up repositories as a different project

- Alan looking at publishing ICDs.  File in repository in json format that records the history, comments of ICD releases.
- Remove ingest script and have that work through the database directly.  Need ability to update from Root (all or selected modules?) or selected latest from a submodule that may not yet have been committed to the Root.