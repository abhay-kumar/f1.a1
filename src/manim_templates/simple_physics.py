#!/usr/bin/env python3
"""
Simple Physics Animation Template - Customizable physics diagram.

A flexible template for creating physics/engineering concept animations.
Customize via params JSON.
"""
from manim import *
import json
import os


class Main(Scene):
    def construct(self):
        # Load params from environment
        params_file = os.environ.get("MANIM_PARAMS_FILE")
        params = {}
        if params_file and os.path.exists(params_file):
            with open(params_file) as f:
                params = json.load(f)

        title_text = params.get("title", "Physics Concept")
        subtitle_text = params.get("subtitle", "")
        show_formula = params.get("show_formula", False)
        formula_text = params.get("formula", "F = ma")
        explanation = params.get("explanation", "")
        highlight_color = params.get("highlight_color", "#FFFF00")

        # Title
        title = Text(title_text, font_size=52, color=WHITE)
        title.to_edge(UP, buff=0.8)
        self.play(Write(title))

        if subtitle_text:
            subtitle = Text(subtitle_text, font_size=28, color=GRAY)
            subtitle.next_to(title, DOWN, buff=0.3)
            self.play(Write(subtitle))

        self.wait(0.5)

        # Main content area
        if show_formula:
            # Display the formula prominently
            formula = MathTex(formula_text, font_size=80)
            formula.move_to(ORIGIN)
            self.play(Write(formula), run_time=1.5)
            self.wait(0.5)

            # Highlight box around formula
            box = SurroundingRectangle(
                formula,
                color=highlight_color,
                buff=0.4,
                stroke_width=4
            )
            self.play(Create(box))

            if explanation:
                # Add explanation below
                explain_text = Text(explanation, font_size=28, color=GRAY)
                explain_text.next_to(box, DOWN, buff=0.5)
                self.play(Write(explain_text))

        self.wait(2)
