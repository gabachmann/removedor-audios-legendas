"""Interface desktop para remover trilhas de áudio e legendas sem recodificar."""
import json
import os
import queue
import subprocess
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

VIDEO_TYPES = [('Vídeos', '*.mkv *.mp4 *.mov *.avi *.webm *.m4v'), ('Todos os arquivos', '*.*')]


def probe_video(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', path],
                            capture_output=True, text=True, check=True, encoding='utf-8', errors='replace')
    return json.loads(result.stdout)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Remove Video Lyrics | Gerenciador de Trilhas')
        self.geometry('920x700')
        self.minsize(720, 560)
        self.configure(fg_color='#0b1220')
        self.video_path = None
        self.streams = []
        self.duration = 0.0
        self.vars = {}
        self.events = queue.Queue()
        self.running = False
        self._build()
        self.after(100, self._poll)

    def _build(self):
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=28, pady=(25, 14))
        ctk.CTkLabel(header, text='REMOVE VIDEO LYRICS', font=ctk.CTkFont(size=26, weight='bold'),
                     text_color='#f8fafc').pack(anchor='w')
        ctk.CTkLabel(header, text='Remova áudios e legendas sem perder a qualidade do vídeo.',
                     font=ctk.CTkFont(size=13), text_color='#94a3b8').pack(anchor='w', pady=(5, 0))

        file_card = ctk.CTkFrame(self, corner_radius=16, fg_color='#172235')
        file_card.pack(fill='x', padx=28, pady=10)
        ctk.CTkLabel(file_card, text='ARQUIVO DE ENTRADA', text_color='#94a3b8',
                     font=ctk.CTkFont(size=12, weight='bold')).pack(anchor='w', padx=20, pady=(18, 6))
        file_row = ctk.CTkFrame(file_card, fg_color='transparent')
        file_row.pack(fill='x', padx=20, pady=(0, 18))
        self.file_label = ctk.CTkLabel(file_row, text='Nenhum vídeo selecionado', anchor='w',
                                       text_color='#e2e8f0')
        self.file_label.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.open_btn = ctk.CTkButton(file_row, text='Selecionar vídeo', width=160, command=self._choose)
        self.open_btn.pack(side='right')

        tracks_card = ctk.CTkFrame(self, corner_radius=16, fg_color='#172235')
        tracks_card.pack(fill='both', expand=True, padx=28, pady=10)
        toolbar = ctk.CTkFrame(tracks_card, fg_color='transparent')
        toolbar.pack(fill='x', padx=20, pady=(17, 8))
        ctk.CTkLabel(toolbar, text='Trilhas encontradas', font=ctk.CTkFont(size=18, weight='bold')).pack(side='left')
        self.count_label = ctk.CTkLabel(toolbar, text='0 selecionadas', text_color='#94a3b8')
        self.count_label.pack(side='right')
        actions = ctk.CTkFrame(tracks_card, fg_color='transparent')
        actions.pack(fill='x', padx=20, pady=(0, 8))
        for label, kind, state in [('Marcar áudios', 'audio', True), ('Marcar legendas', 'subtitle', True),
                                   ('Desmarcar tudo', None, False)]:
            ctk.CTkButton(actions, text=label, width=128, height=30, fg_color='#27364c',
                          hover_color='#334c6c', command=lambda k=kind, s=state: self._mark(k, s)).pack(side='left', padx=(0, 8))
        self.list_frame = ctk.CTkScrollableFrame(tracks_card, fg_color='#101a2b', corner_radius=10)
        self.list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.empty_label = ctk.CTkLabel(self.list_frame, text='Selecione um arquivo para visualizar as trilhas.',
                                        text_color='#94a3b8')
        self.empty_label.pack(pady=35)

        footer = ctk.CTkFrame(self, fg_color='transparent')
        footer.pack(fill='x', padx=28, pady=(8, 26))
        self.status = ctk.CTkLabel(footer, text='Pronto para começar', text_color='#94a3b8', anchor='w')
        self.status.pack(fill='x')
        self.progress = ctk.CTkProgressBar(footer, height=10)
        self.progress.pack(fill='x', pady=(7, 14))
        self.progress.set(0)
        self.save_btn = ctk.CTkButton(footer, text='Remover trilhas selecionadas e salvar', height=44,
                                      font=ctk.CTkFont(weight='bold'), command=self._save, state='disabled')
        self.save_btn.pack(fill='x')

    def _choose(self):
        path = filedialog.askopenfilename(title='Selecionar vídeo', filetypes=VIDEO_TYPES)
        if not path:
            return
        self.video_path = path
        self.file_label.configure(text=Path(path).name)
        self.status.configure(text='Analisando trilhas...')
        self.open_btn.configure(state='disabled')
        self.save_btn.configure(state='disabled')
        threading.Thread(target=self._probe_worker, args=(path,), daemon=True).start()

    def _probe_worker(self, path):
        try:
            data = probe_video(path)
            self.events.put(('probe', path, data))
        except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            self.events.put(('error_probe', str(exc)))

    def _show_streams(self, data):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.vars.clear()
        self.streams = data.get('streams', [])
        try:
            self.duration = float(data.get('format', {}).get('duration') or 0)
        except (TypeError, ValueError):
            self.duration = 0.0
        for stream in self.streams:
            kind = stream.get('codec_type')
            if kind not in ('video', 'audio', 'subtitle'):
                continue
            idx = stream.get('index')
            tags = stream.get('tags') or {}
            name = {'video': 'VÍDEO', 'audio': 'ÁUDIO', 'subtitle': 'LEGENDA'}[kind]
            lang = tags.get('language', 'não informado')
            codec = stream.get('codec_name', 'desconhecido')
            title = tags.get('title', '')
            detail = f'Trilha {idx}  •  {name}  •  {lang}  •  {codec}' + (f'  •  {title}' if title else '')
            row = ctk.CTkFrame(self.list_frame, fg_color='#1b2a40', corner_radius=8)
            row.pack(fill='x', padx=6, pady=5)
            if kind == 'video':
                ctk.CTkLabel(row, text='▣  ' + detail + '  •  preservada', anchor='w',
                             text_color='#9fb2c9').pack(fill='x', padx=14, pady=13)
            else:
                var = ctk.BooleanVar(value=False)
                self.vars[idx] = (var, kind)
                ctk.CTkCheckBox(row, text=detail, variable=var, command=self._refresh,
                                font=ctk.CTkFont(size=13)).pack(anchor='w', padx=14, pady=13)
        if not self.streams:
            ctk.CTkLabel(self.list_frame, text='Nenhuma trilha encontrada.').pack(pady=30)
        self.status.configure(text=f'{len(self.streams)} trilha(s) identificada(s)')
        self._refresh()

    def _mark(self, kind, value):
        if self.running:
            return
        for var, stream_kind in self.vars.values():
            if kind is None or stream_kind == kind:
                var.set(value)
        self._refresh()

    def _refresh(self):
        n = sum(var.get() for var, _ in self.vars.values())
        self.count_label.configure(text=f'{n} selecionada(s) para remover')
        self.save_btn.configure(state='normal' if n and not self.running else 'disabled')

    def _save(self):
        indices = [idx for idx, (var, _) in self.vars.items() if var.get()]
        if not indices or not self.video_path:
            return
        ext = Path(self.video_path).suffix
        out = filedialog.asksaveasfilename(title='Salvar vídeo sem as trilhas',
                                            defaultextension=ext, initialfile=Path(self.video_path).stem + '_limpo' + ext,
                                            filetypes=[('Mesmo formato do original', '*' + ext), ('Todos os arquivos', '*.*')])
        if not out:
            return
        if os.path.normcase(os.path.abspath(out)) == os.path.normcase(os.path.abspath(self.video_path)):
            messagebox.showerror('Arquivo de saída inválido', 'Escolha um caminho diferente do vídeo original.')
            return
        if not messagebox.askyesno('Confirmar remoção', f'Remover {len(indices)} trilha(s) e salvar em:\n{out}?'):
            return
        if os.path.exists(out) and not messagebox.askyesno('Sobrescrever arquivo', 'O arquivo já existe. Deseja substituí-lo?'):
            return
        self.running = True
        self.open_btn.configure(state='disabled')
        self.save_btn.configure(state='disabled')
        self.progress.set(0)
        self.status.configure(text='Processando vídeo...')
        duration = self.duration
        threading.Thread(target=self._process_worker, args=(self.video_path, out, indices, duration), daemon=True).start()

    def _process_worker(self, source, target, indices, duration):
        command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-progress', 'pipe:1', '-nostats',
                   '-n', '-i', source, '-map', '0']
        for idx in indices:
            command += ['-map', f'-0:{idx}']
        command += ['-c', 'copy', target]
        # O usuário já confirmou a substituição, então removemos a saída antes de executar.
        # Evita usar -y inadvertidamente sobre qualquer outro arquivo.
        try:
            if os.path.exists(target):
                os.remove(target)
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, encoding='utf-8', errors='replace')
            for line in process.stdout:
                if line.startswith('out_time=') and duration > 0:
                    stamp = line.partition('=')[2].strip()
                    try:
                        hours, minutes, seconds = stamp.split(':')
                        elapsed = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                        self.events.put(('progress', min(elapsed / duration, 0.99)))
                    except (ValueError, OverflowError):
                        pass
            stderr = process.stderr.read()
            code = process.wait()
            if code != 0:
                raise RuntimeError(stderr.strip() or f'FFmpeg terminou com código {code}')
            self.events.put(('done', target))
        except (OSError, RuntimeError) as exc:
            self.events.put(('error_process', str(exc)))

    def _poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == 'probe':
                    self.open_btn.configure(state='normal')
                    if event[1] == self.video_path:
                        self._show_streams(event[2])
                elif kind == 'error_probe':
                    self.open_btn.configure(state='normal')
                    self.status.configure(text='Falha ao analisar arquivo')
                    messagebox.showerror('Erro ao analisar vídeo', event[1])
                elif kind == 'progress':
                    self.progress.set(event[1])
                    self.status.configure(text=f'Processando... {event[1]:.0%}')
                elif kind in ('done', 'error_process'):
                    self.running = False
                    self.open_btn.configure(state='normal')
                    self._refresh()
                    if kind == 'done':
                        self.progress.set(1)
                        self.status.configure(text='Concluído com sucesso')
                        messagebox.showinfo('Concluído', f'Vídeo salvo em:\n{event[1]}')
                    else:
                        self.status.configure(text='Falha no processamento')
                        messagebox.showerror('Erro no processamento', event[1])
        except queue.Empty:
            pass
        self.after(100, self._poll)


if __name__ == '__main__':
    App().mainloop()
