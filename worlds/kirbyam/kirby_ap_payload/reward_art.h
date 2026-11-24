#ifndef KIRBYAM_REWARD_ART_H
#define KIRBYAM_REWARD_ART_H
#include <stdint.h>

#define AP_REWARD_FX __attribute__((noinline, long_call, section(".aprewardfx")))

/* A visual effect only: this API never records checks or grants rewards. */
AP_REWARD_FX void ap_show_room_reward_gem(uint16_t room, int32_t x, int32_t y,
                                          uint32_t stop_hub_bit);
AP_REWARD_FX void ap_show_player_reward_gem(uint16_t room);

#endif
