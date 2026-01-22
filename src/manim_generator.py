#!/usr/bin/env python3
"""
Manim Generator - Programmatic physics/math animations.

Uses Manim (Mathematical Animation Engine) to create precise,
educational animations for physics and engineering concepts.

Manim is the animation engine used by 3Blue1Brown.

Available diagram types:
- venturi_effect: Ground effect airflow visualization
- f1_car_airflow: F1 car aerodynamics overview
- downforce_comparison: Comparing downforce sources
- tire_degradation: Tire wear over laps
- g_force_visualization: G-forces in corners
- engine_power_curve: Power/torque curves
- brake_energy: Brake energy recovery
- corner_apex: Racing line through a corner
"""
import os
import sys
import json
import shutil
import argparse
import subprocess
import tempfile
from typing import Tuple, Optional, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import FRAME_RATE

# Check if Manim is available
try:
    import manim
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False

# Template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "manim_templates")

# Pre-built diagram types
DIAGRAM_TEMPLATES = {
    "venturi_effect": {
        "file": "venturi.py",
        "description": "Ground effect venturi tunnel visualization",
        "default_duration": 8
    },
    "f1_car_airflow": {
        "file": "f1_airflow.py",
        "description": "F1 car aerodynamic airflow overview",
        "default_duration": 10
    },
    "downforce_comparison": {
        "file": "downforce.py",
        "description": "Wing vs floor downforce comparison",
        "default_duration": 8
    },
    "tire_degradation": {
        "file": "tire_deg.py",
        "description": "Tire compound degradation over laps",
        "default_duration": 6
    },
    "g_force_visualization": {
        "file": "g_force.py",
        "description": "G-forces experienced in corners",
        "default_duration": 6
    },
    "simple_physics": {
        "file": "simple_physics.py",
        "description": "Generic physics animation template",
        "default_duration": 5
    }
}


def generate_manim_segment(diagram_type: str, params: Dict,
                           output_path: str, duration: float = None) -> Tuple[bool, Optional[str]]:
    """
    Generate a Manim animation.

    Args:
        diagram_type: Type of diagram (must exist in DIAGRAM_TEMPLATES)
        params: Parameters to pass to the template
        output_path: Where to save the output video
        duration: Override default duration

    Returns:
        (success, error)
    """
    if not MANIM_AVAILABLE:
        return False, "Manim not installed. Run: pip install manim"

    if diagram_type not in DIAGRAM_TEMPLATES:
        available = list(DIAGRAM_TEMPLATES.keys())
        return False, f"Unknown diagram type: {diagram_type}. Available: {available}"

    template_info = DIAGRAM_TEMPLATES[diagram_type]
    template_file = os.path.join(TEMPLATE_DIR, template_info["file"])

    if not os.path.exists(template_file):
        return False, f"Template file not found: {template_file}. Run setup to create templates."

    # Use default duration if not specified
    if duration is None:
        duration = template_info.get("default_duration", 5)

    # Create temp directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write params to JSON for template to read
        params_file = os.path.join(temp_dir, "params.json")
        params["duration"] = duration
        with open(params_file, "w") as f:
            json.dump(params, f)

        print(f"  Generating Manim animation: {diagram_type}")
        print(f"  Params: {params}")

        # Run manim
        cmd = [
            "manim",
            "-qh",  # High quality
            "--fps", str(FRAME_RATE),
            "-o", "output.mp4",
            "--media_dir", temp_dir,
            template_file,
            "Main"  # Scene name
        ]

        # Set environment for params
        env = os.environ.copy()
        env["MANIM_PARAMS_FILE"] = params_file

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        # Find output file (Manim has nested output structure)
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".mp4"):
                    source = os.path.join(root, file)
                    shutil.copy2(source, output_path)
                    print(f"  Generated: {output_path}")
                    return True, None

        # If no file found, return error
        error_msg = result.stderr[:500] if result.stderr else "Unknown Manim error"
        return False, f"Manim output not found. Error: {error_msg}"


def generate_placeholder_manim(diagram_type: str, output_path: str,
                               duration: float = 5) -> Tuple[bool, Optional[str]]:
    """
    Generate a placeholder video when Manim templates aren't available.
    """
    import subprocess

    label = DIAGRAM_TEMPLATES.get(diagram_type, {}).get("description", diagram_type)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x1a1a2e:s=1920x1080:d={duration}:r={FRAME_RATE}",
        "-vf", (
            f"drawtext=text='[Manim Diagram]':fontcolor=white:fontsize=48:"
            f"x=(w-text_w)/2:y=100:font=monospace,"
            f"drawtext=text='{label}':fontcolor=0x00d4ff:fontsize=36:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:font=monospace"
        ),
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(output_path):
        print(f"  Generated placeholder: {output_path}")
        return True, None

    return False, result.stderr[:300] if result.stderr else "Placeholder generation failed"


def setup_templates():
    """Create the manim_templates directory with basic templates."""
    os.makedirs(TEMPLATE_DIR, exist_ok=True)

    # Create venturi effect template
    venturi_template = '''#!/usr/bin/env python3
"""
Venturi Effect Animation - Shows how ground effect works in F1.
"""
from manim import *
import json
import os

class Main(Scene):
    def construct(self):
        # Load params
        params_file = os.environ.get("MANIM_PARAMS_FILE")
        params = {}
        if params_file and os.path.exists(params_file):
            with open(params_file) as f:
                params = json.load(f)

        show_pressure = params.get("show_pressure_gradient", True)
        animate_flow = params.get("animate_flow", True)

        # Title
        title = Text("The Venturi Effect", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # Ground (track surface)
        ground = Line(LEFT * 6, RIGHT * 6, color=GRAY)
        ground.shift(DOWN * 2)
        ground_label = Text("Track Surface", font_size=20, color=GRAY)
        ground_label.next_to(ground, DOWN)
        self.play(Create(ground), Write(ground_label))

        # F1 floor simplified shape (converging-diverging channel)
        floor_points = [
            LEFT * 4 + UP * 0.3,
            LEFT * 1 + DOWN * 0.5,  # Throat (narrowest point)
            RIGHT * 4 + UP * 0.3
        ]
        floor_top = VMobject()
        floor_top.set_points_smoothly(floor_points)
        floor_top.set_color(RED)
        floor_top.shift(DOWN * 0.5)

        floor_label = Text("F1 Car Floor", font_size=20, color=RED)
        floor_label.next_to(floor_top, UP, buff=0.3)

        self.play(Create(floor_top), Write(floor_label))
        self.wait(0.5)

        # Section labels
        inlet_label = Text("Inlet", font_size=24, color=BLUE)
        inlet_label.move_to(LEFT * 3.5 + UP * 1.5)

        throat_label = Text("Throat", font_size=24, color=GREEN)
        throat_label.move_to(UP * 1.5)

        diffuser_label = Text("Diffuser", font_size=24, color=BLUE)
        diffuser_label.move_to(RIGHT * 3.5 + UP * 1.5)

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

            # Create air particles
            for wave in range(3):
                particles = VGroup()
                for i in range(5):
                    particle = Dot(color=BLUE, radius=0.08)
                    y_offset = -1.2 - i * 0.1
                    particle.move_to(LEFT * 5 + UP * y_offset)
                    particles.add(particle)

                self.add(particles)

                # Animate through venturi
                self.play(
                    particles.animate.move_to(RIGHT * 5 + DOWN * 1.2),
                    run_time=1.5,
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

            # High pressure at inlet (red)
            high_p = Arrow(LEFT * 3 + DOWN * 2.8, LEFT * 3 + DOWN * 1.3, color=RED, buff=0)
            high_label = Text("High P", font_size=18, color=RED)
            high_label.next_to(high_p, DOWN, buff=0.1)

            # Low pressure at throat (blue)
            low_p = Arrow(ORIGIN + DOWN * 1, ORIGIN + DOWN * 2.5, color=BLUE_C, buff=0)
            low_label = Text("LOW P", font_size=18, color=BLUE_C)
            low_label.next_to(low_p, LEFT, buff=0.1)

            self.play(Create(high_p), Write(high_label))
            self.play(Create(low_p), Write(low_label))

            # Suction effect
            suction = Arrow(ORIGIN + DOWN * 2.3, ORIGIN + DOWN * 1.2, color=YELLOW,
                          buff=0, stroke_width=8)
            suction_label = Text("SUCTION = DOWNFORCE", font_size=24, color=YELLOW)
            suction_label.next_to(suction, RIGHT, buff=0.2)

            self.play(Create(suction), Write(suction_label))

        self.wait(2)
'''

    # Create simple physics template
    simple_physics_template = '''#!/usr/bin/env python3
"""
Simple Physics Animation Template - Customizable physics diagram.
"""
from manim import *
import json
import os

class Main(Scene):
    def construct(self):
        # Load params
        params_file = os.environ.get("MANIM_PARAMS_FILE")
        params = {}
        if params_file and os.path.exists(params_file):
            with open(params_file) as f:
                params = json.load(f)

        title_text = params.get("title", "Physics Concept")
        subtitle_text = params.get("subtitle", "")
        show_formula = params.get("show_formula", False)
        formula_text = params.get("formula", "F = ma")

        # Title
        title = Text(title_text, font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))

        if subtitle_text:
            subtitle = Text(subtitle_text, font_size=28, color=GRAY)
            subtitle.next_to(title, DOWN)
            self.play(Write(subtitle))

        self.wait(0.5)

        # Main visualization area
        if show_formula:
            formula = MathTex(formula_text, font_size=72)
            formula.move_to(ORIGIN)
            self.play(Write(formula))
            self.wait(1)

            # Box around formula
            box = SurroundingRectangle(formula, color=YELLOW, buff=0.3)
            self.play(Create(box))

        self.wait(2)
'''

    # Write templates
    with open(os.path.join(TEMPLATE_DIR, "venturi.py"), "w") as f:
        f.write(venturi_template)

    with open(os.path.join(TEMPLATE_DIR, "simple_physics.py"), "w") as f:
        f.write(simple_physics_template)

    # Create __init__.py
    with open(os.path.join(TEMPLATE_DIR, "__init__.py"), "w") as f:
        f.write('"""Manim templates for F1.ai visual generation."""\n')

    print(f"Created Manim templates in: {TEMPLATE_DIR}")
    return True


def list_diagram_types():
    """List available diagram types and their parameters."""
    print("Available Manim diagram types:")
    print("=" * 60)

    for name, info in DIAGRAM_TEMPLATES.items():
        template_path = os.path.join(TEMPLATE_DIR, info["file"])
        exists = os.path.exists(template_path)
        status = "OK" if exists else "MISSING"

        print(f"\n  [{status}] {name}")
        print(f"      Description: {info['description']}")
        print(f"      Duration: {info['default_duration']}s")
        print(f"      Template: {info['file']}")


def main():
    parser = argparse.ArgumentParser(description='Generate Manim animations')
    parser.add_argument('--type', help='Diagram type')
    parser.add_argument('--params', help='JSON params string')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--duration', type=float, help='Duration in seconds')
    parser.add_argument('--list', action='store_true', help='List available types')
    parser.add_argument('--setup', action='store_true', help='Create template directory')
    parser.add_argument('--status', action='store_true', help='Check Manim availability')
    parser.add_argument('--placeholder', action='store_true',
                        help='Generate placeholder if template unavailable')
    args = parser.parse_args()

    if args.status:
        print("Manim Generator Status")
        print("=" * 40)
        print(f"Manim installed: {'Yes' if MANIM_AVAILABLE else 'No'}")
        print(f"Template directory: {TEMPLATE_DIR}")
        print(f"Templates exist: {'Yes' if os.path.exists(TEMPLATE_DIR) else 'No'}")

        if not MANIM_AVAILABLE:
            print("\nInstall Manim with: pip install manim")
            print("Note: Manim requires LaTeX and FFmpeg")
        return

    if args.setup:
        setup_templates()
        return

    if args.list:
        list_diagram_types()
        return

    if args.type and args.output:
        params = json.loads(args.params) if args.params else {}

        # Check if template exists
        template_info = DIAGRAM_TEMPLATES.get(args.type, {})
        template_file = os.path.join(TEMPLATE_DIR, template_info.get("file", ""))

        if not os.path.exists(template_file):
            if args.placeholder:
                print(f"Template not found, generating placeholder...")
                success, error = generate_placeholder_manim(args.type, args.output, args.duration or 5)
            else:
                print(f"Template not found: {template_file}")
                print("Run --setup to create templates, or use --placeholder")
                sys.exit(1)
        else:
            success, error = generate_manim_segment(args.type, params, args.output, args.duration)

        if success:
            print(f"Generated: {args.output}")
        else:
            print(f"Failed: {error}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
