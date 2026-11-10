#pragma once
#include <string.h>

/* DOS device BSTR lengths may include the terminating NUL. */
static inline int zu_usb_device_name(const unsigned char *name) {
    const unsigned n = sizeof("usbscsi.device") - 1;
    return (name[0] == n || (name[0] == n + 1 && name[n + 1] == 0)) &&
           memcmp(name + 1, "usbscsi.device", n) == 0;
}
