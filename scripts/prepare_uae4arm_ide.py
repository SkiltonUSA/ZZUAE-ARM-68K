"""Adapt pinned UAE IDE PIO to the single Core1 worker and host block service."""
def prepare(source):
 s=source
 s=s.replace('static void process_rw_command (struct ide_hdf *ide)','static void do_process_rw_command(struct ide_hdf *ide);\nstatic void do_process_packet_command(struct ide_hdf *ide);\nstatic void process_rw_command (struct ide_hdf *ide)')
 s=s.replace('write_comm_pipe_u32 (&ide->its->requests, ide->num, 1);','do_process_rw_command(ide);')
 s=s.replace('write_comm_pipe_u32 (&ide->its->requests, ide->num | 0x100, 1);','ide_fail(ide); /* ATAPI is not attached in this port. */')
 start=s.index('static int ide_thread (');end=s.index('void ide_initialize',start)
 s=s[:start]+s[end:]
 # Only PIO disks are attached. Discard CD allocation and snapshots entry points.
 s=s[:s.index('void remove_ide_unit(')]
 s=s.replace('scsi_emulate_analyze (ide->scsi);','abort();').replace('scsi_emulate_cmd (ide->scsi);','abort();')
 # Upstream ignores host failures; never acknowledge a failed read/write as success.
 for op in ('read','write'):
  import re
  pat=r'hdf_'+op+r'\s*\(&ide->hdhfd.hfd, ide->secbuf, ide->start_lba \* ide->blocksize, ide->start_nsec \* ide->blocksize\);'
  s,n=re.subn(pat,'if (hdf_'+op+'(&ide->hdhfd.hfd, ide->secbuf, ide->start_lba * ide->blocksize, ide->start_nsec * ide->blocksize) != ide->start_nsec * ide->blocksize) {ide_fail_err(ide, IDE_ERR_UNC);return;}',s)
  assert n==1
 return s
