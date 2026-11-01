# Streamlit Community Cloud deployment

No cloud deployment has yet been verified. Localhost addresses in historical evidence are local test URLs only.

1. Sign in to Streamlit Community Cloud with the GitHub account authorised to access `Miuccia-hub/Juriscloud-agent`.
2. Create an app using this repository, branch `main`, entry point `app.py`. Choose Python 3.12 in advanced settings. Dependencies are in root `requirements.txt`.
3. The model key should be supplied by each visitor in Settings. Confirm that the selected endpoint supports the two configured model names, Responses structured output and web search. If a compatible endpoint is needed, the administrator can configure `OPENAI_BASE_URL` privately.
4. Optional: configure `PKULAW_TOKEN` as a top-level secret through Streamlit's secret settings. Do not commit `.streamlit/secrets.toml` or the local backend Token file. PKULAW access/quota remains the administrator's responsibility.
5. Verify deployment loads, model connection succeeds, a synthetic contract can be uploaded, a report is generated, a follow-up works and an export opens. Do not describe these cloud checks as passed before actually running them.
6. Add the actual HTTPS app URL prominently to README. Verify the instructor can access both the app and the private repository. Invite the teacher after obtaining the correct GitHub username; do not change repository visibility merely to bypass access setup.
7. Resolve the specified course Credentials module requirement and provide the exact live-test input before final submission. Stop editing after formal submission as required by the assignment.

Reference: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
