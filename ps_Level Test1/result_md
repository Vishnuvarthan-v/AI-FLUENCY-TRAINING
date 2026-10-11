# Agentic RAG Helpdesk — Run Results

## Test Results

| # | Tools called (in order) | Agent's answer (short) | Correct? (Y/N) | If N, why? |
|---|---|---|---|---|
| 1 | `search_handbook` | Late fee is Rs. 100 per day, maximum Rs. 2,000 per semester. Source: `fee_policy.md`. | Y | — |
| 2 | `search_handbook` | Hostel residents must return by 9:00 PM. Source: `hostel_rules.md`. | Y | — |
| 3 | `check_exam_eligibility` | Eligible with condonation; Rs. 500 per course. | Y | — |
| 4 | `search_handbook` | CGPA of 6.5 or higher, with no standing arrears. Source: `placement_policy.md`. | Y | — |
| 5 | None | The agent answered Paris. | N | The agent answered from general knowledge instead of rejecting a question outside the college handbook. The relevance guard was not implemented in the executed version. |

## Model Configuration

- **Provider:** Groq
- **Model used:** `openai/gpt-oss-120b`
- **Embedding provider:** FastEmbed
- **Embedding model:** `BAAI/bge-small-en-v1.5`
- **MAX_DISTANCE:** Not configured in the executed version

## Similarity Scores

- **Placements question:** Not measured
- **France question:** Not measured

The executed version uses `store.similarity_search(query, k=3)`, which does not return similarity scores. Therefore, the scores cannot be recovered from this terminal output.

## Additional Verification

### Exam eligibility tool tests

| Attendance | Actual result | Status |
|---:|---|---|
| 82% | `ELIGIBLE` | Pass |
| 70% | `CONDONATION` — Rs. 500 per course | Pass |
| 50% | `NOT ELIGIBLE` | Pass |
| 120% | `ERROR` — attendance must be between 0 and 100 | Pass |

### Conversation memory

- Thread `student-1`: 22 messages saved.
- Thread `student-2`: 2 messages saved.
- Thread `task-run`: Five questions executed sequentially using the same thread ID.

### Conclusion

The agent correctly answered the four college-related questions using the appropriate tools. The France question exposed a limitation: the executed version did not prevent answers to questions outside the handbook. The relevance guard must be implemented and tested before claiming that this requirement passes.
