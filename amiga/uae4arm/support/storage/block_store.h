#pragma once
/* Private ARM cache and copy-on-write area; no raw device writes. */
#define ZN_BLOCK_BYTES 4096u
#define ZN_OVERLAY_BLOCKS 1024u
#define ZN_OVERLAY_HEADER (16u+ZN_OVERLAY_BLOCKS*4u)
#define ZN_OVERLAY_BYTES (ZN_OVERLAY_HEADER+ZN_OVERLAY_BLOCKS*ZN_BLOCK_BYTES)
typedef int (*zn_sector_reader)(void *,unsigned,unsigned,unsigned char *);
int zn_storage_attach_source(unsigned sectors,zn_sector_reader,void *,unsigned char *,unsigned);
unsigned zn_storage_overlay_size(void);
