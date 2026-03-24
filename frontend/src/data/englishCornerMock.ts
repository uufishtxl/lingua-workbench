export interface TutorFeedback {
    polished_text: string;
    explanation_cn: string;
}

export interface CharacterReply {
    content: string;
    audio_url: string | null;
}

export interface PracticeMessage {
    id: number;
    role: 'user' | 'ai';
    status: 'PENDING' | 'SUCCESS' | 'FAILED';
    is_processed: boolean;
    sender_name?: string;
    avatar?: string;

    // User part: Now contains Tutor Feedback (about this specific message)
    user_content?: string;
    user_audio_url?: string | null;
    tutor_feedback?: TutorFeedback;

    // AI part: Focusing on the character identity
    character_reply?: CharacterReply;

    // Extra for frontend rendering
    timestamp: string;
}

export interface WordNode {
    id: string;
    label: string;
    type: 'phrase' | 'topic' | 'keyword';
    explanation: string;
    example: string;
    category?: number; // for ECharts color mapping
    mastery: number;   // 0-100
    frequency: number; // 0-100
    box_level: number; // 1-5 (SRS box)
    embedding?: number[]; // Vector for semantic linking
}

export interface WordLink {
    source: string;
    target: string;
    relation: string;
}

export interface GraphData {
    nodes: WordNode[];
    links: WordLink[];
}

export interface Scenario {
    id: number;
    title: string;
    description: string;
    icon: string;
    system_prompt?: string;
}

export interface ConversationDetail {
    id: number;
    scenario_id: number;
    scenario_title: string;
    status: 'active' | 'completed';
    summary: string;
    messages: PracticeMessage[];
}

export const mockScenarios: Scenario[] = [
    { id: 1, title: "Technical Interview", description: "Practice technical concepts and experience.", icon: "💻" },
    { id: 2, title: "Coffee Chat", description: "Informal networking and small talk.", icon: "☕" },
    { id: 3, title: "Design Review", description: "Presenting UI/UX ideas and receiving feedback.", icon: "🎨" },
];

export const mockConversation: ConversationDetail = {
    id: 1024,
    scenario_id: 1,
    scenario_title: "Technical Writing Contract Interview",
    status: 'active',
    summary: "Senior candidate explaining their pivot to technical writing and strategy for chaotic documentation.",
    messages: [
        {
            id: 5001,
            role: 'ai',
            sender_name: 'Emily (Recruiter)',
            avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emily',
            status: 'SUCCESS',
            is_processed: true,
            character_reply: {
                content: "You have nearly two decades of hardcore software development experience. Why are you applying for a short-term gig right now?",
                audio_url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            },
            timestamp: "2026-03-12T10:00:00Z"
        },
        {
            id: 5002,
            role: 'user',
            sender_name: 'You',
            avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix',
            status: 'SUCCESS',
            is_processed: true,
            user_content: "Job market is brutal. I want to polish my technical writing skills and keep my momentum.",
            tutor_feedback: {
                polished_text: "To be honest, the job market is quite brutal right now. I see this short-term gig as a great opportunity to polish my technical writing skills and keep my momentum going.",
                explanation_cn: "使用 'quite brutal' 增强语气，'momentum going' 是非常地道的搭配，表示保持前进的势头。"
            },
            timestamp: "2026-03-12T10:01:00Z"
        },
        {
            id: 5003,
            role: 'ai',
            sender_name: 'Emily (Recruiter)',
            avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emily',
            status: 'SUCCESS',
            is_processed: true,
            character_reply: {
                content: "I see. Our internal documentation is a complete disaster. We need someone who can hit the ground running. How do you make sense of a chaotic system quickly?",
                audio_url: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
            },
            timestamp: "2026-03-12T10:02:15Z"
        },
        {
            id: 5004,
            role: 'user',
            sender_name: 'You',
            avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix',
            status: 'SUCCESS',
            is_processed: true,
            user_content: "I use AI tools to generate high-level overview. Then I sift through notes to find technical nuggets.",
            tutor_feedback: {
                polished_text: "I heavily leverage AI tools to generate a high-level overview. Once I have that mental map, I sift through the unstructured data to find useful technical nuggets.",
                explanation_cn: "leverage 比 use 更具‘杠杆利用’的专业感；'mental map' 表示脑海中的框架图；'technical nuggets' 是指‘技术干货’。"
            },
            timestamp: "2026-03-12T10:03:00Z"
        }
    ]
};

export const mockGraphData: GraphData = {
    nodes: [
        { id: "1", label: "short-term gig", type: "phrase", explanation: "A temporary job or contract role.", example: "I see this short-term gig as a great opportunity.", category: 0, mastery: 85, frequency: 40, box_level: 4 },
        { id: "2", label: "momentum", type: "keyword", explanation: "Strength or force gained by motion or by a series of events.", example: "It's important to keep my momentum going.", category: 2, mastery: 60, frequency: 70, box_level: 3 },
        { id: "3", label: "hit the ground running", type: "phrase", explanation: "To start something with immediate energy and effectiveness.", example: "We need someone who can hit the ground running.", category: 0, mastery: 40, frequency: 90, box_level: 2 },
        { id: "4", label: "up-to-speed", type: "phrase", explanation: "Moving as fast as something or someone else; fully informed.", example: "It gets me up-to-speed in hours instead of weeks.", category: 0, mastery: 95, frequency: 50, box_level: 5 },
        { id: "5", label: "technical nuggets", type: "phrase", explanation: "Small but valuable pieces of technical information.", example: "I sift through the data to find technical nuggets.", category: 0, mastery: 30, frequency: 30, box_level: 1 },
        { id: "6", label: "human search engines", type: "phrase", explanation: "An annoying situation where engineers are treated as tools for simple queries.", example: "Developers hate being treated like human search engines.", category: 0, mastery: 20, frequency: 20, box_level: 1 },
        { id: "7", label: "mental map", type: "keyword", explanation: "A person's point-of-view perception of their area of interaction.", example: "Once I have that mental map, I can work independently.", category: 2, mastery: 75, frequency: 60, box_level: 3 },
        { id: "8", label: "executive buy-in", type: "phrase", explanation: "Approval or support from management.", example: "The ROI for getting executive buy-in is massive.", category: 0, mastery: 55, frequency: 80, box_level: 3 },
        { id: "9", label: "bottom line", type: "topic", explanation: "The most important factor; the final profit or loss.", example: "Stakeholders care about their bottom line.", category: 1, mastery: 90, frequency: 85, box_level: 5 },
        { id: "10", label: "engineering jargon", type: "topic", explanation: "Technical language used by engineers that is hard for outsiders.", example: "Don't drown stakeholders in engineering jargon.", category: 1, mastery: 45, frequency: 35, box_level: 2 }
    ],
    links: [
        { source: "1", target: "2", relation: "goal" },
        { source: "3", target: "4", relation: "outcome" },
        { source: "7", target: "5", relation: "enables" },
        { source: "6", target: "8", relation: "obstacle" },
        { source: "9", target: "10", relation: "contrast" },
        { source: "8", target: "9", relation: "driver" }
    ]
};
