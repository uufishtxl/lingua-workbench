/**
 * Audio utilities for extracting audio segments using Web Audio API
 */

/**
 * 从音频 URL 中提取指定时间段的音频片段
 * @param audioUrl 音频文件 URL
 * @param startTime 开始时间（秒）
 * @param endTime 结束时间（秒）
 * @returns WAV 格式的 Blob
 */
export async function extractAudioSegment(
    audioUrl: string,
    startTime: number,
    endTime: number
): Promise<Blob> {
    // 1. 获取音频文件
    const response = await fetch(audioUrl);
    const arrayBuffer = await response.arrayBuffer();

    // 2. 解码音频数据
    const audioContext = new AudioContext();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

    // 3. 计算要提取的采样范围
    const sampleRate = audioBuffer.sampleRate;
    const startSample = Math.floor(startTime * sampleRate);
    const endSample = Math.floor(endTime * sampleRate);
    const segmentLength = endSample - startSample;

    // 4. 创建新的 AudioBuffer 存储片段
    const numberOfChannels = audioBuffer.numberOfChannels;
    const segmentBuffer = audioContext.createBuffer(
        numberOfChannels,
        segmentLength,
        sampleRate
    );

    // 5. 复制指定时间段的数据
    for (let channel = 0; channel < numberOfChannels; channel++) {
        const channelData = audioBuffer.getChannelData(channel);
        const segmentData = segmentBuffer.getChannelData(channel);
        for (let i = 0; i < segmentLength; i++) {
            segmentData[i] = channelData[startSample + i]!;
        }
    }

    // 6. 编码为 WAV 格式
    const wavBlob = audioBufferToWav(segmentBuffer);

    // 7. 关闭 AudioContext
    await audioContext.close();

    return wavBlob;
}

/**
 * 将 AudioBuffer 编码为 WAV 格式的 Blob
 */
function audioBufferToWav(audioBuffer: AudioBuffer): Blob {
    const numberOfChannels = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    const format = 1; // PCM
    const bitDepth = 16;

    // 交错多通道数据
    let interleaved: Float32Array;
    if (numberOfChannels === 2) {
        const left = audioBuffer.getChannelData(0);
        const right = audioBuffer.getChannelData(1);
        interleaved = new Float32Array(left.length + right.length);
        for (let i = 0; i < left.length; i++) {
            interleaved[i * 2] = left[i]!;
            interleaved[i * 2 + 1] = right[i]!;
        }
    } else {
        interleaved = audioBuffer.getChannelData(0);
    }

    // 创建 WAV 文件
    const dataLength = interleaved.length * (bitDepth / 8);
    const buffer = new ArrayBuffer(44 + dataLength);
    const view = new DataView(buffer);

    // WAV 文件头
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + dataLength, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // fmt chunk size
    view.setUint16(20, format, true);
    view.setUint16(22, numberOfChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numberOfChannels * (bitDepth / 8), true);
    view.setUint16(32, numberOfChannels * (bitDepth / 8), true);
    view.setUint16(34, bitDepth, true);
    writeString(view, 36, 'data');
    view.setUint32(40, dataLength, true);

    // 写入音频数据
    const offset = 44;
    for (let i = 0; i < interleaved.length; i++) {
        const sample = Math.max(-1, Math.min(1, interleaved[i]!));
        const intSample = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
        view.setInt16(offset + i * 2, intSample, true);
    }

    return new Blob([buffer], { type: 'audio/wav' });
}

function writeString(view: DataView, offset: number, string: string): void {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}
