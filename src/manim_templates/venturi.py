#!/usr/bin/env python3
"""
Venturi Effect Animation - Shows how ground effect works in F1.

This animation demonstrates the Bernoulli principle as applied to
F1 car floors, showing how air accelerates through a narrow gap
creating low pressure and downforce.
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

        show_pressure = params.get("show_pressure_gradient", True)
        animate_flow = params.get("animate_flow", True)
        duration = params.get("duration", 8)

        # Colors
        F1_RED = "#E8002D"
        F1_BLUE = "#3671C6"

        # Title
        title = Text("The Venturi Effect", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # Ground (track surface)
        ground = Line(LEFT * 6, RIGHT * 6, color=GRAY, stroke_width=4)
        ground.shift(DOWN * 2)
        ground_label = Text("Track Surface", font_size=20, color=GRAY)
        ground_label.next_to(ground, DOWN, buff=0.15)
        self.play(Create(ground), Write(ground_label))

        # F1 floor simplified shape (converging-diverging channel)
        floor_points = [
            LEFT * 4 + UP * 0.3,
            LEFT * 2 + DOWN * 0.1,
            LEFT * 0.5 + DOWN * 0.5,  # Throat (narrowest point)
            RIGHT * 2 + DOWN * 0.1,
            RIGHT * 4 + UP * 0.5      # Diffuser exit
        ]
        floor_top = VMobject()
        floor_top.set_points_smoothly(floor_points)
        floor_top.set_color(F1_RED)
        floor_top.set_stroke(width=5)
        floor_top.shift(DOWN * 0.5)

        floor_label = Text("F1 Car Floor", font_size=20, color=F1_RED)
        floor_label.next_to(floor_top, UP, buff=0.4)

        self.play(Create(floor_top), Write(floor_label))
        self.wait(0.5)

        # Section labels
        inlet_label = Text("Inlet", font_size=24, color=F1_BLUE)
        inlet_label.move_to(LEFT * 3.5 + UP * 1.2)

        throat_label = Text("Throat", font_size=24, color=GREEN_C)
        throat_label.move_to(UP * 1.2)

        diffuser_label = Text("Diffuser", font_size=24, color=F1_BLUE)
        diffuser_label.move_to(RIGHT * 3.5 + UP * 1.2)

        self.play(
            Write(inlet_label),
            Write(throat_label),
            Write(diffuser_label)
        )

        # Airflow animation
        if animate_flow:
            self.wait(0.5)

            flow_text = Text("Air accelerates through narrow gap", font_size=24, color=YELLOW)
            flow_text.to_edge(DOWN, buff=0.5)
            self.play(Write(flow_text))

            # Create multiple waves of air particles
            for wave in range(3):
                particles = VGroup()
                for i in range(6):
                    particle = Dot(color=BLUE_B, radius=0.06)
                    y_offset = -1.1 - i * 0.12
                    particle.move_to(LEFT * 5 + UP * y_offset)
                    particles.add(particle)

                self.add(particles)

                # Create path for particles (speed up at throat)
                path = VMobject()
                path.set_points_smoothly([
                    LEFT * 5 + DOWN * 1.3,
                    LEFT * 2 + DOWN * 1.4,
                    ORIGIN + DOWN * 1.6,  # Compressed at throat
                    RIGHT * 2 + DOWN * 1.4,
                    RIGHT * 5 + DOWN * 1.1,
                ])

                self.play(
                    MoveAlongPath(particles, path),
                    run_time=1.2,
                    rate_func=rate_functions.ease_in_out_sine
                )
                self.remove(particles)

            self.play(FadeOut(flow_text))

        # Pressure gradient visualization
        if show_pressure:
            self.wait(0.3)

            pressure_title = Text("Pressure Distribution", font_size=28, color=WHITE)
            pressure_title.to_edge(DOWN, buff=0.5)
            self.play(Write(pressure_title))
            self.wait(0.3)

            # High pressure at inlet (shown as compression)
            high_p_arrow = Arrow(
                LEFT * 3 + DOWN * 2.8,
                LEFT * 3 + DOWN * 1.4,
                color=RED,
                buff=0,
                stroke_width=6
            )
            high_p_label = Text("High P", font_size=18, color=RED)
            high_p_label.next_to(high_p_arrow, DOWN, buff=0.1)

            # Low pressure at throat (suction zone)
            low_p_arrow = Arrow(
                ORIGIN + DOWN * 1.0,
                ORIGIN + DOWN * 2.4,
                color=BLUE_C,
                buff=0,
                stroke_width=6
            )
            low_p_label = Text("LOW P", font_size=20, color=BLUE_C, weight=BOLD)
            low_p_label.next_to(low_p_arrow, LEFT, buff=0.15)

            self.play(Create(high_p_arrow), Write(high_p_label))
            self.wait(0.2)
            self.play(Create(low_p_arrow), Write(low_p_label))
            self.wait(0.3)

            # Suction effect - the key takeaway
            suction_arrow = Arrow(
                ORIGIN + DOWN * 2.2,
                ORIGIN + DOWN * 1.1,
                color=YELLOW,
                buff=0,
                stroke_width=10
            )

            suction_box = Rectangle(
                width=6, height=0.8,
                color=YELLOW,
                fill_opacity=0.2
            )
            suction_box.next_to(suction_arrow, RIGHT, buff=0.3)

            suction_text = Text("SUCTION = DOWNFORCE", font_size=26, color=YELLOW)
            suction_text.move_to(suction_box)

            self.play(Create(suction_arrow))
            self.play(FadeIn(suction_box), Write(suction_text))

            self.wait(0.5)

            # Conclusion
            self.play(FadeOut(pressure_title))

            conclusion = Text(
                "Low pressure creates downforce without drag from wings",
                font_size=24,
                color=WHITE
            )
            conclusion.to_edge(DOWN, buff=0.5)
            self.play(Write(conclusion))

        self.wait(2)
