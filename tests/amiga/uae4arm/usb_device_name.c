#include "usb_device_name.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
    const unsigned char normal[] = "\016usbscsi.device";
    const unsigned char terminated[] = "\017usbscsi.device";
    const unsigned char suffix[] = "\017usbscsi.deviceX";
    const unsigned char other[] = "\016buddha.device";
    const unsigned char empty[] = {0};
    assert(zu_usb_device_name(normal));
    assert(zu_usb_device_name(terminated));
    assert(!zu_usb_device_name(suffix));
    assert(!zu_usb_device_name(other));
    assert(!zu_usb_device_name(empty));
    puts("PASS USB device BSTR with and without counted NUL");
    return 0;
}
