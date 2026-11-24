"""Rita text i källpixelboxar, med lokal emoji-font när den behövs."""
import re
from pathlib import Path
from PIL import ImageFont

FONTROT=Path('C:/Windows/Fonts')


def rita(draw,item,sx,sy):
    st=item['stil'];size=max(8,round(st['storlek_px']*sy));font=ImageFont.truetype(str(FONTROT/st['font']),size)
    emoji=ImageFont.truetype(str(FONTROT/'seguiemj.ttf'),size)
    x,y,width,_=item['box'];width*=sx
    def runs(text):return [(p,emoji if any(ord(c)>0xffff for c in p) else font) for p in re.split(r'([\U00010000-\U0010ffff])',text) if p]
    def measure(text):return sum(f.getlength(p) for p,f in runs(text))
    lines=[]
    for paragraph in item['text'].split('\n'):
        line=''
        for word in paragraph.split():
            candidate=(line+' '+word).strip()
            if line and measure(candidate)>width:lines.append(line);line=word
            else:line=candidate
        lines.append(line)
    advance=font.getbbox('A')[3]+round(size*.15)
    top=font.getbbox(lines[0] or 'A')[1]
    for i,line in enumerate(lines):
        tx=x*sx;length=measure(line)
        if st['justering']=='center':tx+=(width-length)/2
        elif st['justering']=='hoger':tx+=width-length
        for part,f in runs(line):
            args=dict(font=f,fill=st['farg'],stroke_width=round(st['kontur_px']*sy),stroke_fill=st['kontur_farg'])
            if f is emoji:args.update(embedded_color=True,stroke_width=0)
            draw.text((tx,y*sy-top+i*advance),part,**args);tx+=f.getlength(part)
