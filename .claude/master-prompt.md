ok focus on the ERP aspect of the project I have identified 3 key pain points that ucar stuggles with that I want the solution to cover

# the key point is missing kpi dashboard

I want the app to be centralized around a kpi system that governs decision making and institue ranking, there is no current centralized kpi system so we will be calculating it from a set of documents provided by each institute, provide kpis that figure in the international ranking of universities these are the ones I could come up with (enrich if possible)

employment rate: generated though linkedin scraping and institute survey

external relations: conventions avec institue a lexterieur, collaboration avec entreprises, pfe, stages, mobilité, echange, double diplome etc

fincance: gestion de budget, magazin, equipements, bilans de projets, fiches de paiy

academic: taux de reussite, h index du profs, coverage de curriculum (professor hours vs minimum hours per module), double diplomes, faculty research, doctorants, certifications etc

extra cerricular: club activities, events etc

accreditation: iso compliance 21001:2018, governance

human resources: professor hours (overwork/underworked), professor matching, professor per student, documents per administrator

filter out the metrics that do not figure in renouned university rankings and add missing ones (give a complete rational

Looking at this ISO 21001:2018 checklist, here are the KPIs that can be extracted, organized by domain:
Academic Quality
Success Index (graduated batch)
Academic Performance Index
End Semester Exam pass rates & improvement trends
MID I & II consolidated marks availability
Lesson plan completion rate (% approved by HOD)
Faculty Record Book (FRB) completion rate
Syllabus coverage % (internal vs. external experts)
Student-Teacher Ratio (target: 1:20)
Student Outcomes & Engagement
Placement rate (in-campus, off-campus, higher studies)
Placement & Higher Studies Assessment Point
Co-curricular/extracurricular participation rate
Weak student identification & remediation rate
Absenteeism rate & corrective action follow-through
Student counseling record completeness
Faculty & Staff
Training needs identification & fulfillment rate (teaching + non-teaching)
FDP/Workshop attendance count
Staff pursuing higher studies count
Faculty publications (research & other)
Expertise & skill mapping completion
Faculty contribution to external activities
Infrastructure & Resources
Equipment maintenance compliance rate (routine + preventive)
Breakdown maintenance response rate
Calibration compliance rate (internal & external)
Computer maintenance & antivirus update rate
Backup data availability
Fire safety & first aid equipment functionality
Governance & Compliance
Document control compliance (obsolete docs removed, files labeled)
ISO 21001 awareness rate among faculty
Internal audit NCR closure rate
Risk register update status
Risk mitigation action proportionality score
BOS/DAB/PAC/IAAB meeting frequency & minutes availability
Curriculum & Design
Stakeholder input integration rate (PEOs, curriculum)
Curriculum/syllabus distribution with HOD sign-off
Controlled document issuance compliance
Feedback & Continuous Improvement
Parent feedback collection rate
Alumni feedback action closure rate
Graduate exit feedback action rate
Employer feedback action rate
Student class committee discrepancy resolution rate
3-year trend: success index, academic index, placement point (TGR & TGW tracking)
Research & External Engagement
Funded R&D project count
Consultancy revenue/project count
Continuing education course records
Professional society activity count (conferences, seminars, workshops, guest lectures)

the dashboard is required to rank individual institues under ucar and most importantly ucar itself as a whole

# Document ingestion and migration

I want tools to process legacy documents (pdfs, scan document, docx, sheets) and integrate them into a relational?(there may be some unstructured documents with some unifying factors that can be expressed as a non relational table with required fields for processing) i need visual grounding
the documents can be unified around template documents that dictate where the docments will be classified and tagged for mass migration for example
elaborate on this part in detail and suggest the best stategies
I have gathered documents from multiple universities to seed this process, use them as a basis for hypotheses

# Professor and staff management

dashboard for individual professor performance (professor name, specializations, hours, pay, rank, min hours, extra hours, h index, degrees, current position, prev positions, publications_fk)
professor matching capabilities for institutes, embassoador programs, promotions
there are 2 types of professors contractual and permanant
the permanant process is posting open positions where ucar and the ministry opens a concours that selects a certain number of professor to fill the vacancies, the professors pass the test and select their desired institues (4 choices) and they will be selected afterwards, the selection is done manually, now this will be automated

as for contractual (majority in insat) the university itself takes care of the process where they will open candidate positions where professors can upload a dossier that will be the criteria for their selection, they will pass to an interview that will determine their outcome, this can be automated and digitalized as well

# project matching dashboard selon les kpi des institues

assignement des projets par merit, process unifié to post projects and suggest best maches with kpi and previous projects and institute needs

# institute alerts for critical failures and regression

alert ucar for missing documents, comliance issues and misbehavior and falling behind required kpis with automated predictive warnings and call to action

# nice to haves

automatically genenrated reports and emails for alerts and shortcomings (mini audit generation)
predicted international rank selon les sites renommés et credible
anomaly detection in documents (ocr or human failures)
natural language queries over all the documents
