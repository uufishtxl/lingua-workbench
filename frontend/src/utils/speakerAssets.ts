import avatarAll from '@/assets/avatars/friends_all.png'
import avatarChandler from '@/assets/avatars/friends_chandler.png'
import avatarJoey from '@/assets/avatars/friends_joey.png'
import avatarMonica from '@/assets/avatars/friends_monica.png'
import avatarPhoebe from '@/assets/avatars/friends_phoebe.png'
import avatarRachel from '@/assets/avatars/friends-rachel.png'
import avatarRoss from '@/assets/avatars/friends_ross.png'
import avatarMisc from '@/assets/avatars/friends_misc.png'

const AVATARS: Record<string, string> = {
    'Rachel': avatarRachel,
    'Ross': avatarRoss,
    'Monica': avatarMonica,
    'Chandler': avatarChandler,
    'Joey': avatarJoey,
    'Phoebe': avatarPhoebe,
    'All': avatarAll,
}

const COLORS: Record<string, string> = {
    'Rachel': '#FDA4AF', // Rose-300
    'Ross': '#B45309',   // Amber-700
    'Monica': '#991B1B', // Red-800
    'Chandler': '#FDBA74', // Orange-300
    'Joey': '#FACC15',   // Yellow-400
    'Phoebe': '#FEF08A', // Yellow-200
}

export const DEFAULT_AVATAR = avatarMisc
export const DEFAULT_COLOR = '#D1D5DB' // Gray-300

export function getSpeakerAttributes(name: string) {
    // Fuzzy match logic similar to what was in backend or just simple lookup
    // The backend had: if k.lower() in name.lower()

    let key = 'Misc'
    const lowerName = (name || '').toLowerCase()

    for (const k of Object.keys(AVATARS)) {
        if (lowerName.includes(k.toLowerCase())) {
            key = k
            break
        }
    }

    return {
        avatarUrl: AVATARS[key] || DEFAULT_AVATAR,
        themeColor: COLORS[key] || DEFAULT_COLOR
    }
}
