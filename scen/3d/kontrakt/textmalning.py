"""Rita text i källpixelboxar, med lokal emoji-font när den behövs."""
import re
from pathlib import Path
from PIL import ImageFont

FONTROT=Path('C:/Windows/Fonts')


def layout(item,sx=1,sy=1,canvas=None,saker=False):
    st=item['stil'];size=max(8,round(st['storlek_px']*sy));font=ImageFont.truetype(str(FONTROT/st['font']),size)
    emoji=ImageFont.truetype(str(FONTROT/'seguiemj.ttf'),size)
    x,y,width,_=item['box'];x*=sx;y*=sy;width*=sx
    if saker and canvas:
        marginal=.05*canvas[0];hogermarginal=canvas[0]-marginal
        x=max(marginal,min(x,hogermarginal));width=max(1,min(width,hogermarginal-x))
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
    if saker and canvas:y=min(max(.05*canvas[1],y),canvas[1]-.05*canvas[1]-advance*len(lines))
    result=[]
    for i,line in enumerate(lines):
        tx=x;length=measure(line)
        if st['justering']=='center':tx+=(width-length)/2
        elif st['justering']=='hoger':tx+=width-length
        result.append(dict(text=line,x=tx,y=y-top+i*advance,length=length,runs=runs(line)))
    return result,font,advance,top


def grans(item,sx=1,sy=1):
    rows,_,advance,top=layout(item,sx,sy)
    if not rows:return (item['box'][0]*sx,item['box'][1]*sy,item['box'][0]*sx,item['box'][1]*sy)
    return (min(r['x'] for r in rows),min(r['y']+top for r in rows),max(r['x']+r['length'] for r in rows),max(r['y']+top+advance for r in rows))


def rita(draw,item,sx,sy):
    canvas=getattr(getattr(draw,'_image',None),'size',None)
    rows,_,_,_=layout(item,sx,sy,canvas,True)
    st=item['stil']
    for row in rows:
        tx=row['x']
        for part,f in row['runs']:
            args=dict(font=f,fill=st['farg'],stroke_width=round(st['kontur_px']*sy),stroke_fill=st['kontur_farg'])
            if Path(f.path).name.lower()=='seguiemj.ttf':args.update(embedded_color=True,stroke_width=0)
            draw.text((tx,row['y']),part,**args);tx+=f.getlength(part)
