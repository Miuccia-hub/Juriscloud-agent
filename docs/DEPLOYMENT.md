# Streamlit Community Cloud deployment

Live URL: https://juriscloud-agent.streamlit.app/

Deployed on 2 November 2026 from `Miuccia-hub/Juriscloud-agent`, branch `main`, entry `app.py`, using Python 3.12. The application is public and the GitHub repository remains private. Anonymous access to the English homepage, Get started workbench and settings was verified. Chinese/English interface switching was also verified. The owner subsequently configured `PKULAW_TOKEN` through Cloud Secrets; case and legislation authentication/tool-list checks passed on 2 November 2026 without executing searches. Cloud model execution, report generation, actual follow-up research and exports have not yet been verified with live credentials. No credential value is included in this repository. Localhost addresses in historical evidence remain local test URLs.

The earlier `juriscloud.streamlit.app` application was also made public with explicit owner authorisation to release the workspace's private-app slot.

1. Sign in to Streamlit Community Cloud with the GitHub account authorised to access `Miuccia-hub/Juriscloud-agent`.
2. Create an app using this repository, branch `main`, entry point `app.py`. Choose Python 3.12 in advanced settings. Dependencies are in root `requirements.txt`.
3. The model key should be supplied by each visitor in Settings. Confirm that the selected endpoint supports the two configured model names, Responses structured output and web search. If a compatible endpoint is needed, the administrator can configure `OPENAI_BASE_URL` privately.
4. Optional: configure `PKULAW_TOKEN` as a top-level secret through Streamlit's secret settings. Do not commit `.streamlit/secrets.toml` or the local backend Token file. PKULAW access/quota remains the administrator's responsibility.
5. Verify deployment loads, model connection succeeds, a synthetic contract can be uploaded, a report is generated, a follow-up works and an export opens. Do not describe these cloud checks as passed before actually running them.
6. Add the actual HTTPS app URL prominently to README. Verify the instructor can access both the app and the private repository. Invite the teacher after obtaining the correct GitHub username; do not change repository visibility merely to bypass access setup.
7. Resolve the specified course Credentials module requirement before final submission. Stop editing after formal submission as required by the assignment.

Reference: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
