import sys, json
sys.path.insert(0, '/root/.claude/skills/synced/2647aceb-a845-4b12-90dc-91d8ab71d9a6_7433ad11-26c2-4379-bdad-8cc91f648c3b/meeting-minutes/scripts')
import build_minutes as b

def split(self, aw, ah):
    frame_h = b.PAGE_H - 36 - 72
    if ah < self.MIN_SPLIT and self.height <= frame_h:
        return []
    t = b.split_table(self.n, self.sec)
    t.wrap(aw, ah)
    if sum(t._rowHeights[:3]) > ah:
        return []
    parts = t.split(aw, ah)          # actually break the table by rows
    return (parts + self.callouts) if parts else []
b.Section.split = split

src, out = sys.argv[1], sys.argv[2]
b.build(json.load(open(src, encoding='utf-8')), out)
import pymupdf
d = pymupdf.open(out); print('pages', len(d))
for i, p in enumerate(d): p.get_pixmap(dpi=80).save(f'{sys.argv[3]}/page{i+1}.png')
