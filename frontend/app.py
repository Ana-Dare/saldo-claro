"""Ponto de entrada — dashboard único do SaldoClaro."""

import gradio as gr

from frontend.theme import load_css
from frontend.views.categories import load_categories_screen
from frontend.views.home import build_home, refresh_dashboard
from frontend.views.transactions import load_transactions_screen

with gr.Blocks(
    title="SaldoClaro",
    theme=gr.themes.Base(
        primary_hue="blue",
        neutral_hue="zinc",
    ).set(
        body_background_fill="#0A0A0A",
        body_background_fill_dark="#0A0A0A",
        background_fill_primary="#141414",
        background_fill_primary_dark="#141414",
        background_fill_secondary="#1C1C1C",
        background_fill_secondary_dark="#1C1C1C",
        border_color_primary="#2A2A2A",
        border_color_primary_dark="#2A2A2A",
        block_background_fill="#141414",
        block_background_fill_dark="#141414",
        block_label_text_color="#9AA8B8",
        block_label_text_color_dark="#9AA8B8",
        body_text_color="#E8EEF6",
        body_text_color_dark="#E8EEF6",
        input_background_fill="#0F0F0F",
        input_background_fill_dark="#0F0F0F",
        input_border_color="#2A2A2A",
        input_border_color_dark="#2A2A2A",
        button_primary_background_fill="#5B9BD5",
        button_primary_background_fill_dark="#5B9BD5",
        button_primary_text_color="#0A0A0A",
        button_primary_text_color_dark="#0A0A0A",
    ),
    fill_height=True,
    fill_width=True,
) as demo:
    ui = build_home()

    demo.load(
        refresh_dashboard,
        inputs=[ui["month_state"], ui["year_state"]],
        outputs=ui["dash_outputs"],
    )
    demo.load(
        load_transactions_screen,
        inputs=ui["tx_filters"],
        outputs=ui["tx_outputs"],
    )
    demo.load(
        load_categories_screen,
        inputs=ui["cat_filters"],
        outputs=ui["cat_outputs"],
    )

if __name__ == "__main__":
    demo.queue().launch(
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True,
        css=load_css(),
    )
