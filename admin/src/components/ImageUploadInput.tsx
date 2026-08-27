import { useRef, useState, type ChangeEvent } from 'react';

import { api } from '../api';

type Props = {
  name: string;
  defaultValue?: string | null;
  onError?: (message: string) => void;
};

/**
 * 이미지 URL 입력 + 파일 업로드 버튼.
 * 파일을 고르면 /admin/uploads 로 올리고 서빙 URL을 입력칸에 채운다.
 * (외부 URL 직접 붙여넣기도 그대로 지원)
 */
export function ImageUploadInput({ name, defaultValue, onError }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState(defaultValue ?? '');

  const onPick = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setBusy(true);
    try {
      const res = await api.uploadImage(file);
      if (inputRef.current) inputRef.current.value = res.url;
      setPreview(res.url);
    } catch (err) {
      onError?.(err instanceof Error ? err.message : '이미지 업로드 실패');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="upload-field">
      <div className="upload-row">
        <input
          ref={inputRef}
          name={name}
          type="url"
          defaultValue={defaultValue ?? ''}
          placeholder="https:// 직접 입력 또는 파일 업로드"
          onChange={(e) => setPreview(e.target.value)}
        />
        <label className={`btn ghost sm upload-btn${busy ? ' disabled' : ''}`}>
          {busy ? '업로드 중…' : '파일 업로드'}
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            hidden
            disabled={busy}
            onChange={(e) => void onPick(e)}
          />
        </label>
      </div>
      {preview ? (
        <img
          src={preview}
          alt=""
          className="upload-preview"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = 'none';
          }}
          onLoad={(e) => {
            (e.target as HTMLImageElement).style.display = '';
          }}
        />
      ) : null}
    </div>
  );
}
