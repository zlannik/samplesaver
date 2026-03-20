import pyaudio
import wave
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
from datetime import datetime

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.playing = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.playback_thread = None
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        
        # Default save folder
        self.save_folder = os.path.join(os.path.expanduser("~"), "Desktop", "Sample Saver Recordings")
        os.makedirs(self.save_folder, exist_ok=True)
        
        self.setup_ui()
        self.refresh_recordings()
    
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("Sample Saver")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")
        
        # Main frame
        main_frame = tk.Frame(self.root, padx=10, pady=10, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Recording status
        self.status_label = tk.Label(main_frame, text="READY", 
                                    font=("Segoe UI", 12),
                                    bg="#1e1e1e", fg="#87CEEB")
        self.status_label.pack(pady=(0, 15))
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg="#1e1e1e")
        button_frame.pack(pady=(0, 20))
        
        self.record_btn = tk.Button(button_frame, text="START RECORDING", 
                                  command=self.toggle_recording,
                                  bg="#87CEEB", fg="#2e2e2e", 
                                  font=("Segoe UI", 12, "bold"),
                                  width=25, height=2,
                                  relief="flat", bd=0,
                                  activebackground="#6DB8DB",
                                  highlightthickness=0,
                                  borderwidth=2)
        self.record_btn.pack()
        
        # Separator
        separator = tk.Frame(main_frame, height=2, bg="#3e3e3e")
        separator.pack(fill=tk.X, pady=10)
        
        # Recordings section
        recordings_label = tk.Label(main_frame, text="RECORDINGS", 
                                   font=("Segoe UI", 10),
                                   bg="#1e1e1e", fg="#87CEEB",
                                   anchor="w")
        recordings_label.pack(pady=(0, 5), fill=tk.X)
        
        # Create a custom style for dark scrollbar
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Vertical.TScrollbar",
                       gripcount=0,
                       background="#3e3e3e",
                       troughcolor="#2e2e2e",
                       bordercolor="#1e1e1e",
                       arrowcolor="black",
                       relief="#2e2e2e"
        )
        
        # Frame setup
        listbox_frame = tk.Frame(main_frame, bg="#1e1e1e")
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Scrollbar using ttk
        scrollbar = ttk.Scrollbar(listbox_frame, style="Vertical.TScrollbar", orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Listbox setup
        self.recordings_listbox = tk.Listbox(listbox_frame,
                                            bg="#2e2e2e",
                                            fg="white",
                                            font=("Segoe UI", 9),
                                            selectbackground="#87CEEB",
                                            selectforeground="#2e2e2e",
                                            relief="flat",
                                            highlightthickness=0,
                                            yscrollcommand=scrollbar.set
        )
        self.recordings_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.recordings_listbox.yview)
        
        # Control buttons for recordings
        controls_frame = tk.Frame(main_frame, bg="#1e1e1e")
        controls_frame.pack(fill=tk.X)
        
        self.play_btn = tk.Button(controls_frame, text="PLAY", 
                                  command=self.toggle_playback,
                                  bg="#87CEEB", fg="#2e2e2e", 
                                  font=("Segoe UI", 10, "bold"),
                                  width=12, height=1,
                                  relief="flat", bd=0,
                                  activebackground="#6DB8DB",
                                  highlightthickness=0)
        self.play_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_btn = tk.Button(controls_frame, text="DELETE", 
                                   command=self.delete_recording,
                                   bg="#87CEEB", fg="#2e2e2e", 
                                   font=("Segoe UI", 10, "bold"),
                                   width=12, height=1,
                                   relief="flat", bd=0,
                                   activebackground="#6DB8DB",
                                   highlightthickness=0)
        self.delete_btn.pack(side=tk.RIGHT)
    
    def refresh_recordings(self):
        """Refresh the list of recordings"""
        self.recordings_listbox.delete(0, tk.END)
        
        if not os.path.exists(self.save_folder):
            return
        
        files = [f for f in os.listdir(self.save_folder) if f.endswith('.wav')]
        files.sort(reverse=True)  # Most recent first
        
        for file in files:
            self.recordings_listbox.insert(tk.END, file)
    
    def toggle_recording(self):
        """Toggle between start and stop recording"""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def toggle_playback(self):
        """Toggle between play and stop"""
        if self.playing:
            self.stop_playback()
        else:
            self.play_recording()
    
    def play_recording(self):
        """Play the selected recording"""
        selection = self.recordings_listbox.curselection()
        if not selection:
            messagebox.showwarning("Whoops!", "PLEASE SELECT A RECORDING TO PLAY.")
            return
        
        if self.playing:
            return
        
        filename = self.recordings_listbox.get(selection[0])
        filepath = os.path.join(self.save_folder, filename)
        
        self.playing = True
        self.play_btn.config(text="STOP")
        
        # Start playback in a separate thread
        self.playback_thread = threading.Thread(target=self.playback_audio, args=(filepath,))
        self.playback_thread.daemon = True
        self.playback_thread.start()
    
    def playback_audio(self, filepath):
        """Playback audio file in a separate thread"""
        wf = None
        play_stream = None
        
        try:
            wf = wave.open(filepath, 'rb')
            
            play_stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            data = wf.readframes(self.chunk)
            
            while data and self.playing:
                play_stream.write(data)
                data = wf.readframes(self.chunk)
        
        except Exception as e:
            print(f"Playback error: {e}")
        
        finally:
            # Clean up
            if play_stream:
                try:
                    play_stream.stop_stream()
                    play_stream.close()
                except:
                    pass
            
            if wf:
                try:
                    wf.close()
                except:
                    pass
            
            # Reset UI - schedule on main thread
            self.root.after(0, self.reset_playback_ui)
    
    def stop_playback(self):
        """Stop playing audio"""
        self.playing = False
    
    def reset_playback_ui(self):
        """Reset playback UI elements"""
        self.playing = False
        self.play_btn.config(text="PLAY")
    
    def delete_recording(self):
        """Delete the selected recording"""
        selection = self.recordings_listbox.curselection()
        if not selection:
            messagebox.showwarning("Whoops!", "PLEASE SELECT A RECORDING TO DELETE.")
            return
        
        filename = self.recordings_listbox.get(selection[0])
        
        # Confirm deletion
        result = messagebox.askyesno("CONFIRM DELETE", 
                                    f"ARE YOU SURE YOU WANT TO DELETE:\n{filename}?")
        if not result:
            return
        
        filepath = os.path.join(self.save_folder, filename)
    
        try:
            os.remove(filepath)
            self.refresh_recordings()
        except Exception as e:
            messagebox.showerror("ERROR", f"COULD NOT DELETE RECORDING: {str(e)}")

    def start_recording(self):
        if self.recording:
            return
            
        try:
            # Find stereo mix or default input device
            device_index = self.find_stereo_mix()
            
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk
            )
            
            self.recording = True
            self.frames = []
            
            # Update UI
            self.status_label.config(text="RECORDING...", fg="#ff4444")
            self.record_btn.config(text="STOP RECORDING", bg="#ff4444")
            
            # Start recording thread
            self.record_thread = threading.Thread(target=self.record_audio)
            self.record_thread.start()
            
        except Exception as e:
            messagebox.showerror("ERROR", f"COULD NOT START RECORDING: {str(e)}\n\n"
                               "MAKE SURE 'STEREO MIX' IS ENABLED IN YOUR SOUND SETTINGS.")
    
    def find_stereo_mix(self):
        """Find Stereo Mix device or return default input"""
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if "stereo mix" in info['name'].lower() or "what u hear" in info['name'].lower():
                return i
        
        # If no stereo mix found, try default input
        default_input = self.audio.get_default_input_device_info()
        return default_input['index']
    
    def record_audio(self):
        while self.recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f"Recording error: {e}")
                break
    
    def stop_recording(self):
        if not self.recording:
            return
            
        self.recording = False
        
        # Wait for recording thread to finish
        if hasattr(self, 'record_thread'):
            self.record_thread.join()
        
        # Stop and close stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Save the recording
        self.save_recording()
        
        # Update UI
        self.status_label.config(text="RECORDING SAVED!", fg="#4CAF50")
        self.record_btn.config(text="START RECORDING", bg="#87CEEB")
        
        # Refresh recordings list
        self.refresh_recordings()
        
        # Reset status after 3 seconds
        self.root.after(3000, lambda: self.status_label.config(text="READY", fg="#87CEEB"))
    
    def save_recording(self):
        if not self.frames:
            messagebox.showwarning("WARNING", "NO AUDIO DATA TO SAVE.")
            return
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(self.save_folder, filename)
        
        # Save as WAV file
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
        
        print(f"Recording saved: {filepath}")
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        if self.recording:
            self.stop_recording()
        if self.playing:
            self.playing = False
        self.audio.terminate()
        self.root.destroy()

if __name__ == "__main__":
    # Install required packages first:
    # pip install pyaudio
    
    recorder = AudioRecorder()
    recorder.run()