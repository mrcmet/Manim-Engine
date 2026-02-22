from core.services.variable_parser import VariableParser


class TestVariableParser:
    def test_extract_int(self):
        code = "x = 5\n"
        vars = VariableParser.extract_variables(code)
        assert len(vars) == 1
        assert vars[0].name == "x"
        assert vars[0].value == 5
        assert vars[0].var_type == "int"
        assert vars[0].editable is True

    def test_extract_float(self):
        code = "PI_VAL = 3.14\n"
        vars = VariableParser.extract_variables(code)
        assert len(vars) == 1
        assert vars[0].var_type == "float"

    def test_extract_string(self):
        code = 'TITLE = "Hello World"\n'
        vars = VariableParser.extract_variables(code)
        assert len(vars) == 1
        assert vars[0].var_type == "str"
        assert vars[0].value == "Hello World"

    def test_extract_color_by_name(self):
        code = 'CIRCLE_COLOR = "#FF0000"\n'
        vars = VariableParser.extract_variables(code)
        assert len(vars) == 1
        assert vars[0].var_type == "color"

    def test_extract_tuple(self):
        code = "POSITION = (1, 2, 3)\n"
        vars = VariableParser.extract_variables(code)
        assert len(vars) == 1
        assert vars[0].var_type == "tuple"
        assert vars[0].value == (1, 2, 3)

    def test_extract_bool(self):
        code = "VISIBLE = True\n"
        vars = VariableParser.extract_variables(code)
        assert len(vars) == 1
        assert vars[0].var_type == "bool"

    def test_stops_at_class_def(self):
        code = "x = 5\nclass MyScene:\n    y = 10\n"
        vars = VariableParser.extract_variables(code)
        assert len(vars) == 1
        assert vars[0].name == "x"

    def test_multiple_variables(self):
        code = "RADIUS = 2\nSPEED = 1.5\nCOLOR = '#00FF00'\n"
        vars = VariableParser.extract_variables(code)
        assert len(vars) == 3

    def test_invalid_syntax_returns_empty(self):
        code = "def broken(:\n"
        vars = VariableParser.extract_variables(code)
        assert vars == []

    def test_replace_variable(self):
        code = "x = 5\ny = 10\n"
        result = VariableParser.replace_variable(code, "x", 42)
        assert "x = 42" in result
        assert "y = 10" in result

    def test_replace_preserves_other_lines(self):
        code = "RADIUS = 2\nCOLOR = 'blue'\nclass S: pass\n"
        result = VariableParser.replace_variable(code, "RADIUS", 5)
        assert "RADIUS = 5" in result
        assert "COLOR = 'blue'" in result
        assert "class S: pass" in result
