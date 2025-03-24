import matplotlib.font_manager as fm
for font in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
    f = fm.FontProperties(fname=font)
    print(f.get_name(), "->", font)
