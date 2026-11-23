"""Build the bundled clock-service client; never flashes or changes clocks."""
import os, json, subprocess
from pathlib import Path

def build(root, out, image):
    runtime=json.loads(os.environ.get('BETA_CONTAINER_COMMAND','null'))
    if runtime is None:
        connection=os.environ.get('ZZ_CLOCK_PODMAN_CONNECTION',os.environ.get('ZZ8_PODMAN_CONNECTION',os.environ.get('ZZUAE_PODMAN_CONNECTION','nuflix-converter-root')))
        runtime=['podman','--connection',connection,'run','--rm','--platform','linux/amd64']
    target=out/'ZZClock';target.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(runtime+['-v',str(root)+':/work','-w','/work',image,'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020','-O2','-Wall','-Wextra','-Werror','amiga/common/zzclock/client.c','-lamiga','-o',str(target.relative_to(root))],check=True)
    return target
