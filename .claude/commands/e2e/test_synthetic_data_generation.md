# E2E Test: Synthetic Data Generation

Test LLM-powered synthetic data generation functionality in the Natural Language SQL Interface application.

## User Story

As a developer or data analyst
I want to quickly generate synthetic data rows that match my existing table patterns
So that I can expand my datasets for testing and development without manually creating data

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page title is "Natural Language SQL Interface"
4. **Verify** core UI elements are present:
   - Query input textbox
   - Query button
   - Upload Data button
   - Available Tables section

5. Upload a test CSV file containing sample data (e.g., users.csv with at least 10 rows)
6. **Verify** the table appears in the Available Tables section
7. **Verify** the table displays the correct initial row count
8. **Verify** a "Generate Data" button appears to the left of the export button
9. **Verify** the Generate Data button shows dice icon and "Generate" text
10. Take a screenshot of the table with Generate Data button visible

11. Click the Generate Data button
12. **Verify** the button becomes disabled immediately
13. **Verify** the button text changes to hourglass icon and "Generating..." text
14. **Verify** a loading state is displayed while generation is in progress

15. Wait for generation to complete (allow up to 30 seconds for LLM API call)
16. **Verify** a success notification appears
17. **Verify** the notification message shows "Added 10 rows to [table_name]" or similar
18. **Verify** the table row count has increased by 10 from the initial count
19. **Verify** the Generate Data button is re-enabled after completion
20. Take a screenshot of the success notification

21. Enter a query to view the newly generated data: "SELECT * FROM uploaded_table ORDER BY rowid DESC LIMIT 10"
22. Click the Query button
23. **Verify** query results show 10 new rows
24. **Verify** the generated data has correct column structure matching the table schema
25. **Verify** the generated data values are realistic and match patterns from existing data (e.g., valid emails, proper name formats, appropriate number ranges)
26. Take a screenshot of generated data in query results

27. Test with empty table scenario:
    - Upload a new CSV with only 1 row
    - Click Generate Data button
    - **Verify** generation still works (samples from the single row)
    - **Verify** 10 new rows are generated

28. Test error handling:
    - Try clicking Generate Data button multiple times rapidly
    - **Verify** button remains disabled during generation
    - **Verify** no duplicate requests are sent

29. Test table refresh:
    - Note the current row count
    - Click Generate Data button
    - **Verify** row count updates automatically after generation completes
    - **Verify** no manual page refresh is needed

30. Take a screenshot of the final state

## Success Criteria

- Generate Data button appears to the left of CSV export button for every table
- Button shows dice icon and "Generate" text in default state
- Button shows hourglass icon and "Generating..." text during loading
- Button is disabled during generation process
- Generation completes successfully within 30 seconds
- Success notification displays with correct row count
- Table row count increases by exactly 10 rows
- Generated data matches table schema (correct columns)
- Generated data is realistic and follows patterns from existing data
- Generated data has appropriate types (numbers are numbers, emails are valid format, etc.)
- Button re-enables after generation completes
- Table row count refreshes automatically without page reload
- Works with tables that have minimal sample data (1+ rows)
- No errors occur during the entire process
- 3 screenshots are captured (initial button state, success notification, generated data)
