local default = require("hamster_hamster_state_machine")
local GUN_KICK_TRACK_LINE = default.GUN_KICK_TRACK_LINE

local STATIC_TRACK_LINE = default.STATIC_TRACK_LINE
local MAIN_TRACK = default.MAIN_TRACK
local BOLT_CAUGHT_TRACK = default.BOLT_CAUGHT_TRACK
local bolt_caught_states = default.bolt_caught_states
local main_track_states = default.main_track_states

local gun_kick_state = setmetatable({}, {__index = default.gun_kick_state})
local idle_state = setmetatable({}, {__index = main_track_states.idle})

local function isNoAmmo(context)
    -- 这里同时检查了枪管和弹匣
    return (not context:hasBulletInBarrel()) and (context:getAmmoCount() <= 0)
end

function gun_kick_state.transition(this, context, input)
    if (input == INPUT_SHOOT) then
        local track = context:findIdleTrack(GUN_KICK_TRACK_LINE, false)
        local last_shoot_timestamp = context:getLastShootTimestamp()
        local current_timestamp = context:getCurrentTimestamp()
        local shoot_interval = context:getShootInterval()
        if (current_timestamp - last_shoot_timestamp < shoot_interval + 100) then
            if (context:isCrawl()) then
                context:runAnimation("shoot_bipod", track, true, PLAY_ONCE_STOP, 0)
            else
                context:runAnimation("shoot_auto", track, true, PLAY_ONCE_STOP, 0)
            end
        else
            context:runAnimation("shoot", track, true, PLAY_ONCE_STOP, 0)
        end
    end
    return nil
end

function idle_state.transition(this, context, input)
    if (input == INPUT_RELOAD) then
        if (context:isCrawl()) then
            if (isNoAmmo(context)) then
                context:runAnimation("reload_bipod_empty", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            else
                context:runAnimation("reload_bipod_tactical", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            end
        else
            if (isNoAmmo(context)) then
                context:runAnimation("reload_empty", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            else
                context:runAnimation("reload_tactical", context:getTrack(STATIC_TRACK_LINE, MAIN_TRACK), false, PLAY_ONCE_STOP, 0.2)
            end
        end
        return this.main_track_states.idle
    end
    return main_track_states.idle.transition(this, context, input)
end

local M = setmetatable({
    main_track_states = setmetatable({
        idle = idle_state
    }, {__index = main_track_states}),
    gun_kick_state = gun_kick_state
}, {__index = default})

function M:initialize(context)
    default.initialize(self, context)
end

return M