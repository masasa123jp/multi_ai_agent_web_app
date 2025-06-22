/* frontend/js/file_upload.js
   ─────────────────────────────────────────
   複数ファイルアップロード
*/
import { API } from './api.js';
import { UI  } from './ui.js';

export function initFileUpload(){
  const form = document.getElementById('uploadForm');
  const inp  = document.getElementById('fileInput');
  const list = document.getElementById('uploadList');
  document.getElementById('clearFilesBtn')
          .addEventListener('click', ()=>{ inp.value=''; list.innerHTML=''; });

  form.addEventListener('submit', async ev=>{
    ev.preventDefault();
    if (!inp.files.length){ UI.showErrorToast('ファイルを選択してください'); return;}
    const fd = new FormData();
    [...inp.files].forEach(f=> fd.append('files', f));            // :contentReference[oaicite:15]{index=15}
    try{
      const { uploaded } = await API.uploadFiles(fd);
      list.innerHTML = uploaded.map(f=>
        `<li class="list-group-item"><a href="${f.url}" target="_blank">${f.name}</a></li>`
      ).join('');
      inp.value = '';
      UI.toast('アップロード成功','success');
    }catch(e){ UI.showErrorToast(`アップロード失敗: ${e.message}`); }
  });
}
