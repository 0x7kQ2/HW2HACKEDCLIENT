#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <netinet/in.h>
#include <sys/socket.h>

static int internet_family(const struct sockaddr *address) {
    if (!address)
        return 0;
    if (address->sa_family == AF_INET) {
        const struct sockaddr_in *ipv4 = (const struct sockaddr_in *)address;
        return (ntohl(ipv4->sin_addr.s_addr) >> 24) != 127;
    }
    if (address->sa_family == AF_INET6) {
        const struct sockaddr_in6 *ipv6 = (const struct sockaddr_in6 *)address;
        return !IN6_IS_ADDR_LOOPBACK(&ipv6->sin6_addr);
    }
    return 0;
}

int connect(int fd, const struct sockaddr *address, socklen_t length) {
    static int (*real_connect)(int, const struct sockaddr *, socklen_t);
    if (internet_family(address)) {
        errno = ENETUNREACH;
        return -1;
    }
    if (!real_connect)
        real_connect = dlsym(RTLD_NEXT, "connect");
    return real_connect(fd, address, length);
}

ssize_t sendto(int fd, const void *buffer, size_t size, int flags,
               const struct sockaddr *address, socklen_t length) {
    static ssize_t (*real_sendto)(int, const void *, size_t, int,
                                  const struct sockaddr *, socklen_t);
    if (internet_family(address)) {
        errno = ENETUNREACH;
        return -1;
    }
    if (!real_sendto)
        real_sendto = dlsym(RTLD_NEXT, "sendto");
    return real_sendto(fd, buffer, size, flags, address, length);
}

ssize_t sendmsg(int fd, const struct msghdr *message, int flags) {
    static ssize_t (*real_sendmsg)(int, const struct msghdr *, int);
    if (message && internet_family(message->msg_name)) {
        errno = ENETUNREACH;
        return -1;
    }
    if (!real_sendmsg)
        real_sendmsg = dlsym(RTLD_NEXT, "sendmsg");
    return real_sendmsg(fd, message, flags);
}
