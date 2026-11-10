"""Changing an included pixel worker must invalidate drawing.o."""
import sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
import build_uae4arm as b
with tempfile.TemporaryDirectory(dir=b.ROOT/'.context') as temp:
 out=Path(temp);tree=out/'src'
 for folder in [tree,tree/'include',out/'include']:folder.mkdir(exist_ok=True)
 (tree/'drawing.cpp').write_text('#include "linetoscr.cpp"\n')
 (tree/'linetoscr.cpp').write_text('int pixels(){return 1;}\n')
 (out/'include/sysconfig.h').write_text('')
 with patch.object(b,'OUT',out),patch.object(b,'SRC',tree),patch.object(b,'UP',out),patch.object(b,'prepare',return_value=tree),patch.object(sys,'argv',['build','drawing']),patch.object(b.subprocess,'run') as run:
  run.return_value.returncode=0;run.return_value.stdout='';run.return_value.stderr=''
  assert not b.build();assert run.call_count==1
  assert not b.build();assert run.call_count==1
  (tree/'linetoscr.cpp').write_text('int pixels(){return 2;}\n')
  assert not b.build();assert run.call_count==2,'included pixel source did not invalidate drawing.o'
  assert not b.build();assert run.call_count==2
print('PASS drawing rebuilds only when its inputs change')
