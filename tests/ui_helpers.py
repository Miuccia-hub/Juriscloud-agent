from streamlit.testing.v1 import AppTest

def workspace_app(*args,**kwargs):
    kwargs.setdefault("default_timeout",15)  # Allow cold imports in a fresh local environment.
    app=AppTest.from_file(*args,**kwargs)
    app.session_state["page"]="workspace"
    app.session_state["ui_language"]="中文"  # Existing Chinese-language fixtures.
    return app
