# Version-2 measured results

Synthetic benchmark; see the report for limitations.

| Partition | Model | n | Accuracy | Macro P | Macro R | Macro F1 |
|---|---|---|---|---|---|---|
| validation | majority | 2386 | 0.0503 | 0.0025 | 0.0500 | 0.0048 |
| validation | keywords | 2386 | 0.7330 | 0.8918 | 0.7288 | 0.7868 |
| validation | nltk_nb | 2386 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| validation | logistic_raw | 2386 | 0.9573 | 0.9597 | 0.9519 | 0.9329 |
| validation | logistic_preprocessed | 2386 | 0.9564 | 0.9590 | 0.9509 | 0.9308 |
| validation | logistic_word_char | 2386 | 0.9686 | 0.9700 | 0.9646 | 0.9573 |
| held-out test | majority | 2384 | 0.0503 | 0.0025 | 0.0500 | 0.0048 |
| held-out test | keywords | 2384 | 0.6925 | 0.8778 | 0.6879 | 0.7518 |
| held-out test | nltk_nb | 2384 | 0.9958 | 0.9959 | 0.9952 | 0.9954 |
| held-out test | logistic_raw | 2384 | 0.9723 | 0.9736 | 0.9683 | 0.9633 |
| held-out test | logistic_preprocessed | 2384 | 0.9778 | 0.9787 | 0.9745 | 0.9721 |
| held-out test | logistic_word_char | 2384 | 0.9857 | 0.9862 | 0.9837 | 0.9832 |
| held-out test | hybrid_context | 2384 | 0.9782 | 0.9801 | 0.9783 | 0.9780 |

### Validation extraction (2386 authored examples)

| Method | Field | P | R | F1 | Exact | Gold present |
|---|---|---|---|---|---|---|
| rules | event_name | 0.8753 | 0.8996 | 0.8873 | 0.8630 | 1873 |
| rules | date | 1.0000 | 0.9937 | 0.9968 | 0.9950 | 1891 |
| rules | time | 1.0000 | 0.9925 | 0.9963 | 0.9946 | 1740 |
| rules | venue | 0.9972 | 0.9826 | 0.9898 | 0.9845 | 1834 |
| hybrid | event_name | 0.8875 | 0.9178 | 0.9024 | 0.8772 | 1873 |
| hybrid | date | 1.0000 | 0.9937 | 0.9968 | 0.9950 | 1891 |
| hybrid | time | 1.0000 | 0.9925 | 0.9963 | 0.9946 | 1740 |
| hybrid | venue | 0.9972 | 0.9826 | 0.9898 | 0.9845 | 1834 |

Complete-record accuracy: rules **0.8529**, hybrid **0.8671**.
### Test extraction (2384 authored examples)

| Method | Field | P | R | F1 | Exact | Gold present |
|---|---|---|---|---|---|---|
| rules | event_name | 0.6654 | 0.5469 | 0.6004 | 0.5554 | 1960 |
| rules | date | 1.0000 | 0.9881 | 0.9940 | 0.9904 | 1939 |
| rules | time | 1.0000 | 0.9899 | 0.9949 | 0.9924 | 1785 |
| rules | venue | 0.9681 | 0.9403 | 0.9540 | 0.9312 | 1809 |
| hybrid | event_name | 0.7359 | 0.6071 | 0.6654 | 0.6049 | 1960 |
| hybrid | date | 1.0000 | 0.9881 | 0.9940 | 0.9904 | 1939 |
| hybrid | time | 1.0000 | 0.9899 | 0.9949 | 0.9924 | 1785 |
| hybrid | venue | 0.9637 | 0.9403 | 0.9519 | 0.9279 | 1809 |

Complete-record accuracy: rules **0.5227**, hybrid **0.5638**.
### Actual validation errors

| Method | ID | Field | Expected | Predicted | Input excerpt |
|---|---|---|---|---|---|
| rules | v2-00-49-000 | event_name | harbour creative electronics | None | registration closes on 2 january 2027. announcing the interactive tutorial harbour creative electronics scheduled for 09 dec 2028 at 11:30. participants will build something themse |
| rules | v2-00-49-008 | event_name | coral data storytelling | None | announcing the guided practical session coral data storytelling scheduled for august 31, 2029 at amber community centre. bring a laptop for guided exercises and individual practice |
| rules | v2-01-13-002 | event_name | Coral Modern Biology | None | The department announces "Coral Modern Biology", a seminar on 08 April 2029 at 9:30 PM at Linden Atrium. Listen to a researcher explain recent discoveries, followed by discussion. |
| rules | v2-01-13-006 | event_name | Amber Modern Biology | None | The department announces "Amber Modern Biology", a seminar inside Room 185, Amber Block on January 01, 2027 at 9:45 PM. Listen to a researcher explain recent discoveries, followed  |
| rules | v2-01-13-008 | event_name | linden urban futures | None | the department announces "linden urban futures", a research talk this saturday at 19:30 inside room 161, linden block. listen to a researcher explain recent discoveries, followed b |
| rules | v2-01-44-003 | event_name | Harbour Urban Futures | None | Our scholarly discussion will be Harbour Urban Futures via Google Meet next Friday at 16:30. Listen to a researcher explain recent discoveries, followed by discussion. |
| rules | v2-01-44-010 | event_name | Copper Quantum Horizons | None | Our research talk will be Copper Quantum Horizons on May 01, 2027 at 3:00 PM inside Harbour Cafe. Listen to a researcher explain recent discoveries, followed by discussion. |
| rules | v2-01-49-000 | event_name | amber research methods | None | registration closes on 2 january 2027. announcing the guest lecture amber research methods scheduled for 01 sep 2029 at 5:45 pm. an invited speaker will present findings and answer |
| rules | v2-01-49-002 | event_name | Sapphire Ocean Science | None | Announcing the guest lecture Sapphire Ocean Science at 10:30 at Amber Sports Ground. Listen to a researcher explain recent discoveries, followed by discussion. |
| rules | v2-01-49-006 | event_name | Sapphire Quantum Horizons | None | Announcing the seminar Sapphire Quantum Horizons in Harbour Stadium in 3 days. Listen to a researcher explain recent discoveries, followed by discussion. |
| rules | v2-01-49-009 | event_name | Copper Research Methods | None | Announcing the research talk Copper Research Methods at 9 am. Listen to a researcher explain recent discoveries, followed by discussion. |
| rules | v2-01-49-011 | event_name | Copper Ocean Science | None | Announcing the seminar Copper Ocean Science on 30 June 2027 inside Sapphire Hall. Listen to a researcher explain recent discoveries, followed by discussion. The organizer's office  |
### Actual test errors

| Method | ID | Field | Expected | Predicted | Input excerpt |
|---|---|---|---|---|---|
| rules | v2-00-01-002 | event_name | None | Notice for attendees: a guided practical session | Notice for attendees: a guided practical session will be held today at 9 pm. Participants will build something themselves with help from an instructor. |
| rules | v2-00-01-004 | event_name | None | Notice for attendees: a guided practical session | Notice for attendees: a guided practical session will be held in Willow Meeting Room. Participants will build something themselves with help from an instructor. |
| rules | v2-00-01-011 | event_name | None | Notice for attendees: an interactive tutorial | Notice for attendees: an interactive tutorial will be held on June 15, 2027 at 10:15 AM at Juniper Cafe. Participants will build something themselves with help from an instructor.  |
| rules | v2-00-05-008 | event_name | None | notice for attendees: a guided practical session | notice for attendees: a guided practical session will be held today at 12:45 pm in crimson meeting room. work through practical activities in small groups. |
| rules | v2-00-05-010 | event_name | None | Notice for attendees: a skill-building session | Notice for attendees: a skill-building session will be held on 06 January at 13:30 inside Crimson Garden. Bring a laptop for guided exercises and individual practice. |
| rules | v2-00-06-003 | event_name | Crimson Robotics Lab | None | Please attend the interactive tutorial on Crimson Robotics Lab via Zoom this Saturday at 12:30. Work through practical activities in small groups. |
| rules | v2-00-06-007 | event_name | Crimson Watercolour Basics | None | Registration closes on 2 January 2027. Please attend the interactive tutorial on Crimson Watercolour Basics on 2029-06-09 at 8 am at Room 462, Crimson Block. Bring a laptop for gui |
| rules | v2-00-06-009 | event_name | Willow Watercolour Basics | None | Please attend the hands-on lab on Willow Watercolour Basics. Bring a laptop for guided exercises and individual practice. |
| rules | v2-00-07-000 | event_name | cypress python essentials | None | registration closes on 2 january 2027. cypress python essentials a skill-building session. date: october 22, 2028 time: 12:30 venue: willow atrium work through practical activities |
| rules | v2-00-07-001 | event_name | Willow Design Thinking | None | Willow Design Thinking A skill-building session. Date: 22 November Time: 8 am Venue: Crimson Garden Work through practical activities in small groups. |
| rules | v2-00-07-002 | event_name | Crimson Data Storytelling | None | Crimson Data Storytelling A guided practical session. Date: tomorrow Time: 14:30 Venue: Cypress Studio Participants will build something themselves with help from an instructor. |
| rules | v2-00-07-003 | event_name | Meadow Creative Electronics | None | Meadow Creative Electronics A guided practical session. Date: 13 August 2029 Time: 09:30 Venue: Ivory Atrium Work through practical activities in small groups. |


Separate completed real-data results: [real_review_v1/RESULTS.md](real_review_v1/RESULTS.md). These do not replace the frozen synthetic results.
