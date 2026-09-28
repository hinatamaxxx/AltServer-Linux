// Links the production library, with a synthetic usbmux server and TCP device.
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <libimobiledevice/libimobiledevice.h>

int main(int argc, char** argv)
{
    assert(argc == 3);
    idevice_info_t* list = NULL;
    int count = 0;
    const int valid = atoi(argv[2]);
    const idevice_error_t enumeration = idevice_get_device_list_extended(&list, &count);
    assert(enumeration == (valid ? IDEVICE_E_SUCCESS : IDEVICE_E_NO_DEVICE));
    assert(count == valid);
    if (valid) assert(list[0]->conn_type == CONNECTION_NETWORK);
    idevice_device_list_extended_free(list);
    idevice_t device = NULL;
    const idevice_error_t lookup = idevice_new_with_options(&device,
        "0000000000000000000000000000000000000000", IDEVICE_LOOKUP_NETWORK);
    if (!valid) {
        assert(lookup != IDEVICE_E_SUCCESS && device == NULL);
        return 0;
    }
    assert(lookup == IDEVICE_E_SUCCESS);
    idevice_connection_t connection = NULL;
    const idevice_error_t result = idevice_connect(device, atoi(argv[1]), &connection);
    if (atoi(argv[2])) {
        assert(result == IDEVICE_E_SUCCESS);
        assert(idevice_disconnect(connection) == IDEVICE_E_SUCCESS);
    } else {
        assert(result != IDEVICE_E_SUCCESS);
    }
    idevice_free(device);
    return 0;
}
