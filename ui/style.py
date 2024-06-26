class Style:
    @classmethod
    def set_dark_style(cls, widget):
        background_color = "#21252B"
        text_color = "#ABB2BF"
        border_color = "#33688A"
        button_hover_color = "#2E3743"
        widget.setStyleSheet(f"""
            QTabWidget::pane {{ background: {background_color}; border: 1px solid {border_color}; }}
            QTabBar::tab {{ background: {background_color}; border: 1px solid {border_color}; color: {text_color}; border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 0.5em; }}
            QTabBar::tab:selected {{ background: {background_color}; border-top-color: {text_color}; }}
            QTabBar::tab:hover {{ border-top-color: {text_color}; }}
            QTabBar::tab:!selected {{ margin-top: 2px; }}
            QTabBar::tab:last {{ margin-right: 0; }}
            QTabBar::tab:first {{ margin-left: 0; }}
            QTabBar::tab:selected:!first:!last {{ border-left: 2px solid transparent; border-right: 2px solid transparent; }}
            QTabWidget::tab-bar {{ border-top: 1px solid {border_color}; }}
            QWidget {{ background-color: {background_color}; color: {text_color}; border: 1px solid {border_color}; }}
            QPushButton {{ border-style: outset; }}
            QPushButton:hover {{ border-style: inset; background-color: {button_hover_color}; font-weight: 800; }}
            QGroupBox {{
                border: 1px solid #33688A; /* Adjust border color for dark style */
                border-radius: 5px;
                margin-top: 10px; /* Space at the top of the QGroupBox */
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left; /* Title at the top center */
                padding: 3px 3px;
                margin-top: -8px; /* Adjust this value to bring the title up so it's above the border */
                background-color: {background_color}; /* Adjust background color for dark style */
            }}
        """)
        #TODO: write style to resources/dark.qss


    @classmethod
    def set_light_style(cls, widget):
        widget.setStyleSheet("""
        """)
        #TODO: write style to resources/light.qss

    @classmethod
    def set_custom_style(cls, widget, background_color, text_color, button_hover_color=None):
        button_hover_css = ""
        if button_hover_color:
            button_hover_css = f"QPushButton:hover {{ background-color: {button_hover_color}; font-weight: 800; }}"
        widget.setStyleSheet(
            f"""
            QTabWidget::pane {{ background: {background_color}; border: 1px solid {text_color}; }}
            QTabBar::tab {{ background: {background_color}; border: 1px solid {text_color}; color: {text_color}; border-top-left-radius: 4px; border-top-right-radius: 4px; padding: 0.5em; }}
            QTabBar::tab:selected {{ background: {background_color}; border-top-color: {text_color}; }}
            QTabBar::tab:hover {{ border-top-color: {text_color}; }}
            QTabBar::tab:!selected {{ margin-top: 2px; }}
            QTabBar::tab:last {{ margin-right: 0; }}
            QTabBar::tab:first {{ margin-left: 0; }}
            QTabBar::tab:selected:!first:!last {{ border-left: 2px solid transparent; border-right: 2px solid transparent; }}
            QTabWidget::tab-bar {{ border-top: 1px solid {text_color}; }}
            QWidget {{ background-color: {background_color}; color: {text_color}; border: 1px solid {text_color}; }}
            QPushButton {{ border-style: outset; }}
            {button_hover_css}
            QGroupBox {{
                border: 1px solid {text_color}; /* Adjust border color for dark style */
                border-radius: 5px;
                margin-top: 10px; /* Space at the top of the QGroupBox */
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left; /* Title at the top center */
                padding: 3px 3px;
                margin-top: -8px; /* Adjust this value to bring the title up so it's above the border */
                background-color: {background_color}; /* Adjust background color for dark style */
            }}
            """
        )

        #TODO: write style to resources/custom.qss



