from vpl_parser import VplParser

content = open("vpl_parser_input.txt", "r").read()
expected = open("vpl_parser_expected.txt", "r").read()

units = VplParser.parse_vpl(content)

new_content = "\n".join([VplParser.to_vpl(u) for u in units])
print(new_content == expected)