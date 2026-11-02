"""Localised upload component. Files stay in the current Streamlit session."""
from pathlib import Path
from io import BytesIO
import base64
from uuid import uuid4
import streamlit as st
import streamlit.components.v1 as components

_component = components.declare_component("local_upload",path=str(Path(__file__).resolve().parents[1]/"assets/uploader"))

def decode_files(value, limit):
    items=(value or {}).get("files",[])
    if not isinstance(items,list) or len(items)>limit:
        raise ValueError("最多上传六份补充材料。")
    result=[]
    for item in items:
        data=item.get("data","")
        if not isinstance(data,str) or len(data)>11200000:
            raise ValueError("文件为空或超过 8 MB。请拆分或转换后上传。")
        raw=base64.b64decode(data,validate=True)
        if not raw or len(raw)>8*1024*1024:
            raise ValueError("文件为空或超过 8 MB。请拆分或转换后上传。")
        name=Path(item["name"]).name
        if Path(name).suffix.lower() not in (".docx",".pdf",".txt"):
            raise ValueError("请上传 Word、PDF 或文本文件。")
        file=BytesIO(raw);file.name=name;result.append(file)
    return result

def upload_files(key,label,language,limit):
    saved_key="_files_"+key
    saved=st.session_state.get(saved_key,{"files":[]})
    epoch=st.session_state.setdefault("_upload_epoch",uuid4().hex)
    result=_component(label=label,english=language=="English",limit=limit,initial=saved,
                      default=saved,key=key+epoch)
    # A component can briefly return None while its iframe reconnects during a
    # rerun. Keep the last acknowledged selection instead of dropping the chip.
    if result is not None:
        st.session_state[saved_key]=result
    return decode_files(st.session_state.get(saved_key),limit)
