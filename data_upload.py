import streamlit as st

from processing import carregar_arquivo_externo, validar_arquivo_externo
from database import atualizar_tabela_banco


def mostrar_upload_dados():
    st.subheader("Carregar Dados")
    st.caption("Atualize as bases do dashboard com arquivos CSV ou Excel.")

    st.info(
        "Fluxo automatizado: arquivo → validação → SQLite → processamento → dashboard atualizado."
    )

    tipo_label = st.selectbox(
        "Qual base deseja atualizar?",
        ["Summary", "Timecards", "FX"],
    )
    tipo_base = tipo_label.lower()

    arquivo = st.file_uploader(
        "Selecione um arquivo CSV ou Excel",
        type=["csv", "xlsx", "xls"],
        key="upload_base_fpa",
    )

    if arquivo is None:
        st.caption("Envie um arquivo para iniciar a validação.")
        return

    try:
        df_upload = carregar_arquivo_externo(arquivo)
    except Exception as erro:
        st.error(f"Não foi possível ler o arquivo: {erro}")
        return

    valido, mensagem = validar_arquivo_externo(df_upload, tipo_base)

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows Received", f"{len(df_upload):,}")
    c2.metric("Columns", len(df_upload.columns))
    c3.metric("File Type", arquivo.name.split(".")[-1].upper())

    if not valido:
        st.error(mensagem)
        return

    st.success(mensagem)

    with st.expander("Pré-visualizar arquivo", expanded=True):
        st.dataframe(df_upload.head(20), use_container_width=True, hide_index=True)

    st.divider()

    if tipo_base == "fx":
        st.warning(
            "Para FX, a atualização substitui a tabela atual. Use o arquivo completo de taxas de câmbio."
        )
        modo = "replace"
        st.text_input("Modo de atualização", value="Substituir tabela FX", disabled=True)
    else:
        modo_label = st.radio(
            "Modo de atualização",
            ["Adicionar novos registros", "Substituir a tabela"],
            horizontal=True,
        )
        modo = "append" if modo_label == "Adicionar novos registros" else "replace"

    confirmar = st.checkbox(
        "Confirmo que revisei o arquivo e desejo atualizar o banco."
    )

    if st.button(
        "Atualizar banco",
        type="primary",
        disabled=not confirmar,
        use_container_width=True,
    ):
        try:
            resultado = atualizar_tabela_banco(
                tipo_base=tipo_base,
                novos_dados=df_upload,
                modo=modo,
            )
            st.cache_data.clear()
            st.session_state["banco_atualizado"] = True
            st.success("Banco atualizado com sucesso.")

            a, b, c, d = st.columns(4)
            a.metric("Rows Before", f"{resultado['linhas_antes']:,}")
            b.metric("Rows Received", f"{resultado['linhas_recebidas']:,}")
            c.metric("Rows Now", f"{resultado['linhas_final']:,}")
            d.metric("Duplicates Avoided", f"{resultado['duplicados_evitados']:,}")
        except Exception as erro:
            st.error(f"Erro ao atualizar o banco: {erro}")

    if st.session_state.get("banco_atualizado", False):
        st.caption(
            "O SQLite já foi atualizado. Recarregue o dashboard para recalcular todas as análises."
        )
        if st.button("Recarregar dashboard", use_container_width=True):
            st.session_state["banco_atualizado"] = False
            st.rerun()
