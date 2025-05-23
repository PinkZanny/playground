# -*- coding: utf-8 -*-

# make translate
# make compile
# make clean

import streamlit as st
from sections import market_overview, sip, mean_reversion, market_regime
from data.data_loader import render_searchbar
import gettext
import os
st.set_page_config(page_title="ZANQOR Playground", layout="wide")

def get_translation(lang):
    try:
        trans = gettext.translation(
            domain="base",
            localedir="locales",
            languages=[lang],
            fallback=True,
        )
    except Exception:
        trans = gettext.NullTranslations()
    return trans.gettext

lang_map = {
    "English": "en",
    "Italiano": "it"
}
lang_choice = st.sidebar.selectbox("🌐 Language", list(lang_map.keys()), index=0)
lang_code = lang_map[lang_choice]
if "lang_code" not in st.session_state:
    st.session_state["lang_code"] = lang_code
elif st.session_state["lang_code"] != lang_code:
    st.session_state["lang_code"] = lang_code
    st.rerun()
_ = get_translation(st.session_state["lang_code"])

st.sidebar.title("ZANQOR Playground")
st.sidebar.image("assets/portfolio_logo_variant.png", width=200)

section = st.sidebar.radio(
    _("Choose a section:"), 
    [_("Market Overview"), _("SIP (Should I Panic?)"), _("Mean Reversion Heatmap"), _("Market Regime Detector")]
)

st.sidebar.write(_("Select an asset:"))
with st.sidebar:
    asset = render_searchbar()

st.sidebar.write("I am NOT a financial advisor. Nothing in this app should be considered financial advice. Please do your own research before making any investment decisions.")

if section == _("Market Overview"):
    market_overview.render(asset=asset, _=_)
elif section == _("SIP (Should I Panic?)"):
    sip.render(asset=asset, _=_)
elif section == _("Mean Reversion Heatmap"):
    mean_reversion.render(asset=asset, _=_)
elif section == _("Market Regime Detector"):
    market_regime.render(asset=asset, _=_)
