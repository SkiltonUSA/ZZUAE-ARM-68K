/* Keep hot code past the partially-owned first physical page. The allocation
 * is only 64-byte aligned; an image-relative 4 KiB pad guarantees subsequent
 * instructions lie in fully owned, private-cacheable physical pages. */
ENTRY(_start)
PHDRS { image PT_LOAD FLAGS(7); dynamic PT_DYNAMIC FLAGS(6); }
SECTIONS {
  . = 0;
  .entry : { KEEP(*(.text.entry)) } :image
  . = ALIGN(4096);
  .text : { *(.text*) } :image
  .rodata : { *(.rodata*) } :image
  .data : { *(.data*) *(.got*) } :image
  .dynamic : { *(.dynamic) } :image :dynamic
  .dynsym : { *(.dynsym) } :image
  .dynstr : { *(.dynstr) } :image
  .hash : { *(.hash) } :image
  .gnu.hash : { *(.gnu.hash) } :image
  .rel.dyn : { *(.rel.dyn) } :image
  ASSERT(. < 0x100000, "ARM image overlaps private page tables")
  .bss 0x220000 (NOLOAD) : { *(.bss*) *(COMMON) } :NONE
  /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment) }
  ASSERT(. < 0x17d0000, "PocketSNES BSS overlaps stack reserve")
}
