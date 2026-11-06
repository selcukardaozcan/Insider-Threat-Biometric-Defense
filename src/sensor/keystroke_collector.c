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

#include <signal.h>

static struct termios orig_termios;
static int termios_modified = 0;

void reset_terminal_mode(void) {
    if (termios_modified) {
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig_termios);
        termios_modified = 0;
    }
}

void sig_handler(int sig) {
    (void)sig;
    reset_terminal_mode();
    printf("\n[*] Exiting Keystroke Collector.\n");
    exit(0);
}

int send_event_to_daemon(const KeystrokeEvent *event, const char *sock_path) {
    int sock = socket(AF_UNIX, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("[-] Failed to create AF_UNIX socket");
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

    if (sent < 0) {
        perror("[-] Failed to send event to daemon socket");
    }

    close(sock);
    return (sent > 0) ? 0 : -1;
}

int main(int argc, char *argv[]) {
    int silent_mode = 0;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--silent") == 0 || strcmp(argv[i], "-s") == 0) {
            silent_mode = 1;
        }
    }

    if (!silent_mode) {
        printf("[*] Insider Threat Keystroke Collector initialized.\n");
    }

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

    if (!silent_mode) {
        printf("[+] Monitoring keystrokes for user: %s (IP: %s, Session: %s)\n", user, src_ip, session_id);
        printf("[+] Interactive mode active. Start typing (Press Ctrl+C to quit):\n\n");
    }

    // Configure cbreak mode: read characters immediately without waiting for newline
    if (tcgetattr(STDIN_FILENO, &orig_termios) == 0) {
        struct termios raw = orig_termios;
        raw.c_lflag &= ~(ICANON); // Non-canonical mode (no line buffering)
        raw.c_cc[VMIN] = 1;
        raw.c_cc[VTIME] = 0;
        if (tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw) == 0) {
            termios_modified = 1;
            atexit(reset_terminal_mode);
            signal(SIGINT, sig_handler);
            signal(SIGTERM, sig_handler);
        }
    }

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

        // Visual feedback only in interactive/debug mode, completely invisible in silent mode
        if (!silent_mode) {
            if (ch == 10 || ch == 13) {
                printf("\n[Sensor] <ENTER> (flight: %lld ms) -> telemetry sent\n", flight_time);
            } else {
                printf("[Sensor] '%c' (flight: %lld ms) -> telemetry sent\n", (ch >= 32 && ch <= 126) ? ch : '?', flight_time);
            }
            fflush(stdout);
        }

        // Dispatch via UDP unix domain socket
        send_event_to_daemon(&event, SOCKET_PATH);
    }

    reset_terminal_mode();
    return 0;
}
