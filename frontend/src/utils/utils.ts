export const formatTime = (seconds: string | number): string => {
  const totalSeconds = typeof seconds === 'string' ? parseFloat(seconds) : seconds;
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const remainingSeconds = Math.floor(totalSeconds % 60);

  const pad = (num: number) => num.toString().padStart(2, '0');

  return `${pad(minutes)}:${pad(remainingSeconds)}`;
};