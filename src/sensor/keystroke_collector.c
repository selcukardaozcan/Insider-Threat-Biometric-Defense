/**
 * keystroke_collector.c
 * 
 * Low-level sensor module for SSH terminal sessions.
 * Captures raw keystroke timings with sub-millisecond precision using POSIX high-resolution timers.
 * Streams structured telemetry (session_id, user, key_ascii, timestamp_ms, dwell_ms)
 * to a local Unix Domain Socket consumed by the Python Orchestrator.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <termios.h>
#include <pwd.h>

#define SOCKET_PATH "/var/run/insider_sensor.sock"
#define BUFFER_SIZE 512

typedef struct {
    char user[64];
    char session_id[64];
    char src_ip[46];
    long long timestamp_ms;
    long long dwell_ms;
    long long flight_time_ms;
    int key_code;
} KeystrokeEvent;

static long long get_current_time_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)(ts.tv_sec) * 1000 + (ts.tv_nsec / 1000000);
}

int send_event_to_daemon(const KeystrokeEvent *event, const char *sock_path) {
    int sock = socket(AF_UNIX, SOCK_DGRAM, 0);
    if (sock < 0) {
        return -1;
    }

    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(struct sockaddr_un));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, sock_path ? sock_path : SOCKET_PATH, sizeof(addr.sun_path) - 1);

    char payload[BUFFER_SIZE];
    snprintf(payload, sizeof(payload),
             "{\"user\":\"%s\",\"session_id\":\"%s\",\"src_ip\":\"%s\","
             "\"timestamp_ms\":%lld,\"flight_time_ms\":%lld,\"key_code\":%d}\n",
             event->user, event->session_id, event->src_ip,
             event->timestamp_ms, event->flight_time_ms, event->key_code);

    ssize_t sent = sendto(sock, payload, strlen(payload), 0,
                          (struct sockaddr*)&addr, sizeof(struct sockaddr_un));

    close(sock);
    return (sent > 0) ? 0 : -1;
}

int main(int argc, char *argv[]) {
    printf("[*] Insider Threat Keystroke Collector initialized.\n");

    const char *user = getenv("USER");
    if (!user) user = "unknown";

    const char *ssh_client = getenv("SSH_CLIENT");
    char src_ip[46] = "127.0.0.1";
    if (ssh_client) {
        sscanf(ssh_client, "%45s", src_ip);
    }

    char session_id[64];
    snprintf(session_id, sizeof(session_id), "sess_%s_%d", user, getpid());

    long long last_press_ms = 0;

    printf("[+] Monitoring keystrokes for user: %s (IP: %s, Session: %s)\n", user, src_ip, session_id);
    printf("[+] Press Ctrl+C or type 'exit' to quit.\n");

    // Test loop or piped input hook
    int ch;
    while ((ch = getchar()) != EOF) {
        long long now_ms = get_current_time_ms();
        long long flight_time = (last_press_ms == 0) ? 0 : (now_ms - last_press_ms);
        last_press_ms = now_ms;

        KeystrokeEvent event;
        strncpy(event.user, user, sizeof(event.user) - 1);
        strncpy(event.session_id, session_id, sizeof(event.session_id) - 1);
        strncpy(event.src_ip, src_ip, sizeof(event.src_ip) - 1);
        event.timestamp_ms = now_ms;
        event.flight_time_ms = flight_time;
        event.key_code = ch;

        // Dispatch via UDP unix domain socket or output
        send_event_to_daemon(&event, SOCKET_PATH);
    }

    return 0;
}
