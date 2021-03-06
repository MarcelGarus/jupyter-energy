#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

#include "utils.c"

enum mcp_types
{
    f501,
    f511
};

// Set address pointer to 0xa (active power), read 32 bits
const unsigned char f501_read_active_power[] = {0x41, 0x0, 0xa, 0x44};
const unsigned char f501_read_apparent_power_divisor[] =
    {0x41, 0x00, 0x40, 0x52};
const unsigned char f501_set_apparent_power_divisor[] =
    {0x41, 0x00, 0x40, 0x57, 0x00, 0x03};
const unsigned char f501_set_accumulation_interval[] =
    {0x41, 0x00, 0x5A, 0x57, 0x00, 0x00};
const unsigned char f501_read_range[] = {0x41, 0x00, 0x48, 0x44};

const unsigned char f511_read_active_power[] = {0x41, 0x0, 0x16, 0x4E, 8};
const unsigned char f511_read_active_power1[] = {0x41, 0x0, 0x16, 0x4E, 4};
const unsigned char f511_read_active_power2[] = {0x41, 0x0, 0x1a, 0x4E, 4};
const unsigned char f511_set_accumulation_interval[] =
    {0x41, 0x00, 0xA8, 0x4D, 2, 0x00, 0x00};

enum mcp_states
{
    init,
    wait_ack,
    get_len,
    get_data,
    validate_checksum
};

enum mcp_states mcp_state = wait_ack;

int fd;

int init_serial(const char *port, int baud)
{
    struct termios tty;

    fd = open(port, O_RDWR | O_NOCTTY | O_SYNC);
    if (fd < 0)
    {
        return -1;
    }

    if (tcgetattr(fd, &tty) < 0)
    {
        return -1;
    }

    cfsetospeed(&tty, (speed_t)baud);
    cfsetispeed(&tty, (speed_t)baud);

    tty.c_cflag |= (CLOCAL | CREAD); /* ignore modem controls */
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8;      /* 8-bit characters */
    tty.c_cflag &= ~PARENB;  /* no parity bit */
    tty.c_cflag &= ~CSTOPB;  /* only need 1 stop bit */
    tty.c_cflag &= ~CRTSCTS; /* no hardware flowcontrol */

    /* setup for non-canonical mode */
    tty.c_iflag &=
        ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON);
    tty.c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
    tty.c_oflag &= ~OPOST;

    /* fetch bytes as they become available */
    tty.c_cc[VMIN] = 1;
    tty.c_cc[VTIME] = 1;

    if (tcsetattr(fd, TCSANOW, &tty) != 0)
    {
        return -1;
    }
    return 0;
}

int mcp_cmd(unsigned char *cmd, unsigned int cmd_length, unsigned char *reply, int fd)
{
    if (fd < 0)
    {
        return ERR_INVALID_HANDLE;
    }

    unsigned char buf[80];
    unsigned char command_packet[80];
    int rdlen;
    uint8_t len;
    uint8_t i;
    uint8_t checksum = 0;
    uint8_t datap = 0;

    command_packet[0] = 0xa5;
    command_packet[1] = cmd_length + 3;
    memcpy(command_packet + 2, cmd, cmd_length);
    for (i = 0; i < cmd_length + 2; i++)
    {
        checksum += command_packet[i];
    }
    command_packet[i] = checksum;
    tcflush(fd, TCIOFLUSH);
    len = write(fd, command_packet, cmd_length + 3);
    if (len != cmd_length + 3)
    {
        return ERR_COULDNT_WRITE_TO_MCP;
    }
    tcdrain(fd);
    while (1)
    {
        rdlen = read(fd, buf, 1);
        if (rdlen == 0)
        {
            return ERR_COULDNT_READ_FROM_MCP;
        }
        switch (mcp_state)
        {
        case wait_ack:
            if (buf[0] == 0x06)
            {
                /* Only read commands will return more than an ACK */
                if ((command_packet[5] == 0x44) || (command_packet[5] == 0x52) || (command_packet[5] == 0x4e))
                {
                    mcp_state = get_len;
                }
                else
                {
                    return 0;
                }
            }
            break;
        case get_len:
            len = buf[0];
            /* Workaround for sporadically broken packets, fix me! */
            if (len != 11)
            {
                mcp_state = wait_ack;
                return ERR_MCP_DIDNT_SEND_ACK;
            }
            mcp_state = get_data;
            break;
        case get_data:
            reply[datap++] = buf[0];
            if ((datap + 2) == (len - 1))
            {
                mcp_state = validate_checksum;
            }
            break;
        case validate_checksum:
            mcp_state = wait_ack;
            checksum = 0x06 + len;
            for (i = 0; i < (len - 3); i++)
            {
                checksum += reply[i];
            }
            if (checksum == buf[0])
            {
                return len - 3;
            }
            else
            {
                return ERR_MCP_CHECKSUM_FAILED;
            }
            break;
        default:
            mcp_state = wait_ack;
        }
    }
}

int f511_get_power(int *ch1, int *ch2, int fd)
{
    int res;
    unsigned char reply[40];
    res =
        mcp_cmd((unsigned char *)&f511_read_active_power,
                sizeof(f511_read_active_power), (unsigned char *)&reply, fd);
    if (res > 0)
    {
        *ch1 = (reply[3] << 24) + (reply[2] << 16) + (reply[1] << 8) + reply[0];
        *ch2 = (reply[7] << 24) + (reply[6] << 16) + (reply[5] << 8) + reply[4];
        return 0;
    }
    else
    {
        return res;
    }
}

int f511_init(const char *port)
{
    unsigned char reply[80];
    int res;

    if (init_serial(port, B115200) < 0)
    {
        return -1;
    }
    res =
        mcp_cmd((unsigned char *)f511_set_accumulation_interval,
                sizeof(f511_set_accumulation_interval),
                (unsigned char *)&reply, fd);
    if (res < 0)
        return res;
    return fd;
}
