from manim import *

class CircleAnimation(Scene):
    def construct(self):
        # Create a circle and a square
        circle = Circle(radius=1.5, color=BLUE, fill_opacity=0.5)
        square = Square(side_length=2.5, color=GREEN, fill_opacity=0.3)

        # Title
        title = Text("Manim Engine Test", font_size=40).to_edge(UP)

        # Animate
        self.play(Write(title))
        self.play(Create(circle))
        self.wait(0.5)
        self.play(Transform(circle, square))
        self.wait(0.5)
        self.play(circle.animate.set_color(YELLOW).rotate(PI / 4))
        self.play(FadeOut(circle), FadeOut(title))
