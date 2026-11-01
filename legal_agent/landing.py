"""Public introduction component; does not read documents or call a model."""
from pathlib import Path
import streamlit.components.v1 as components

_landing=components.declare_component('juriscloud_landing',path=str(Path(__file__).resolve().parents[1]/'assets/landing'))

def render_landing(language, reduce_motion):
    return _landing(language=language,reduce_motion=reduce_motion,key='landing',default=None)
