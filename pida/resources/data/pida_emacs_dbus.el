;;; pida_emacs_dbus.el --- PIDA Project
;; Emacs client script for PIDA
;;
;; pida.editors.emacs
;;  ~~~~~~~~~~~~~~~~~~~~
;; 
;;    :license: GPL 2 or later
;;    :copyright: 2007-2009 the Pida Project;; 
;;

(require 'dbus)


;;;Defining constants for dbus
(defconst pida-dbus-ns (concat "uk.co.pida.pida." (getenv "PIDA_DBUS_UUID")))
(defconst pida-dbus-path (concat "uk.co.pida.Emacs." (getenv "PIDA_DBUS_UUID")))
(defconst pida-dbus-interface (concat "uk.co.pida.Emacs." (getenv "PIDA_DBUS_UUID")))

(defconst emacs-dbus-ns (concat "uk.co.pida.Emacs." (getenv "PIDA_DBUS_UUID")))
(defconst emacs-dbus-path (concat "uk.co.pida.Emacs." (getenv "PIDA_DBUS_UUID")))
(defconst emacs-dbus-interface (concat "uk.co.pida.Emacs." (getenv "PIDA_DBUS_UUID")))



(defun pida-register-hooks ()
  "Register hooks to inform pida what is happening in emacs"
  (add-hook 'window-setup-hook
	    'pida-emacs-start)
  (add-hook 'find-file-hooks
 	    'pida-find-file)
  (add-hook 'kill-buffer-hook
 	    'pida-buffer-kill)
  (add-hook 'window-configuration-change-hook
	    'pida-window-configuration-change)
  (add-hook 'kill-emacs-hook
 	    'pida-kill-emacs)
  (add-hook 'after-save-hook
	    'pida-after-save))

(defun pida-unregister-hooks ()
  "Remove all hooks before quitting emacs and pida"
  (remove-hook 'find-file-hooks
	       'pida-find-file)
  (remove-hook 'kill-buffer-hook
	       'pida-kill-buffer)
  (remove-hook 'window-configuration-change-hook
	       'pida-window-configuration-change)
  (remove-hook 'kill-emacs-hook	       
	       'pida-kill-emacs)
  (remove-hook 'after-save-hook
	       'pida-after-save))

(defun pida-connect (port)
  "Called at startup by eval option
   Initializes all needed things"
  (pida-register-hooks)
  (register-dbus)
  (pida-prepare-completion))

(defun pida-stop-cb ()
  "Callback - called from pida to exit emacs
   DBUS method"
  (pida-unregister-hooks)
  (kill-emacs))

(defun pida-frame-setup (frame)
  "Callback - called from pida to hide menu and toolbar
   DBUS method"
  (modify-frame-parameters frame
			   '((menu-bar-lines . nil)))
  (modify-frame-parameters frame
			   '((tool-bar-lines . nil))))

(defun pida-goto-line (bufn line)
  "Callback - go to line in actual buffer
   DBUS method"
  (set-buffer (get-file-buffer bufn))
  (goto-line line))

(defun pida-cut (buffn)
  "Callback - cut the actual marked region
   DBUS method"
  (set-buffer (get-file-buffer buffn))
  (kill-region (region-beginning) (region-end)))

(defun pida-copy (buffn)
  "Callback - copy the region
   DBUS method"
  (set-buffer (get-file-buffer buffn))
  (kill-ring-save (region-beginning) (region-end)))

(defun pida-paste (buffn)
  "Callback - paste from kill-ring
   DBUS method"
  (set-buffer (get-file-buffer buffn))
  (yank))

(defun pida-undo ()
  "Callback - undo the buffer
   DBUS method"
  (let (result) 
    (if (undo)
	(setq result '(:boolean t))
      (setq result '(:boolean nil)))
    result))

(defun pida-open-file (filename)
  "Callback - open a file 
   DBUS method"
  (let (result)
    (if (find-file filename)
	(setq result '(:boolean t))
      (setq result '(:boolean nil)))
    result))

(defun pida-change-buffer (filename)
  "Callback - change to buffer
   DBUS method"
  (let (result)
    (if (switch-to-buffer (get-file-buffer filename))
	(setq result '(:boolean t))
      (setq result '(:boolean nil)))
    result))

(defun pida-kill-buffer (filename)
  "Callback - close the given buffer
   DBUS method"
  (kill-buffer (get-file-buffer filename)))

(defun pida-save-buffer (buffn)
  "Callback - save the current buffer
   DBUS method"
  (set-buffer (get-file-buffer buffn))
  (save-buffer))

(defun pida-set-dir (path)
  "Callback - set the working dir
   DBUS method"
  (cd path))


(defun pida-find-file ()
  "Hook-Method - emacs opens a files
  emits a dbus signal"
  (dbus-send-signal 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "BufferOpen"
   buffer-file-name)
  (pida-set-completion-wrapper)
  )

(defun pida-window-configuration-change ()
  "Hook-Method - emacs changes the buffer
  emits a dbus signal"
  (dbus-send-signal 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "BufferChange"
   buffer-file-name))


(defun pida-buffer-kill ()
  "Hook-Method - emacs killd a buffer
  emits a dbus signal"
  (dbus-send-signal 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "BufferClose"
   buffer-file-name))

(defun pida-after-save ()
  "Hook-Method - emacs saves a buffer
  emits a dbus signal"
  (dbus-send-signal 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "BufferSave"
   buffer-file-name))

(defun pida-kill-emacs ()
  "Hook-Method - emacs opens a files
  emits a dbus signal"
  (dbus-send-signal 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "EmacsKill"))

(defun pida-emacs-start ()
  "Hook-Method - emacs starts
  emits a dbus signal"
  (sit-for 2)
  (dbus-call-method 
   :session
   pida-dbus-ns
   "/uk/co/pida/pida/emacs"
   "uk.co.pida.pida.emacs"
   "EmacsEnter"))

(defun pida-complete (&optional prefix)
  "calling th e pida code assist
   using dbus"
  (setq compl (dbus-call-method :session pida-dbus-ns
 		    "/uk/co/pida/pida/language"
		    "uk.co.pida.pida.language" 
		    "get_completions"
		    "" (buffer-string) (- (point) 1))))

(defun mycomplete-wrapper (prefix maxnum)
  "Wrapper around `pida-complete',
     to use as a `completion-function'."
  (let ((completions (pida-complete prefix)))
    (when maxnum
      (setq completions
	    (butlast completions (- (length completions) maxnum))))
    completions))

(defun pida-set-completion-wrapper ()
  "Setting the completion function -- needsto be done for every buffer"
  (setq completion-function 'mycomplete-wrapper)
)

(defun pida-prepare-completion() 
  "preparing code assists -- load needed libs"
  (setq lp "pida/editors/emacs/share/completion")
  (setq load-path (append (list lp)  load-path))
  (require 'auto-overlay-common)
  (pida-set-completion-wrapper)
  (require 'completion-ui)
  )

(defun pida-emacs-introspect ()
  "Emacs Pida Interface"
  "<node name='/uk/co/pida/Emacs'>
  <interface name='org.freedesktop.DBus.Introspectable'>
   <method name='Introspect'>
      <arg name='xml_data' type='s' direction='out'/>
    </method>
  </interface>
  <interface name='uk.co.pida.Emacs'>
    <signal name='BufferOpen'>
      <arg type='s' name='fileName' />
    </signal>
    <signal name='BufferClose'>
      <arg type='s' name='fileName' />
    </signal>
    <signal name='BufferSave'>
      <arg type='s' name='fileName' />
    </signal>
    <signal name='BufferChnage'>
      <arg type='s' name='fileName' />
    </signal>
    <signal name='EmacsKill'>
    </signal>
    <method name='OpenFile'>
      <arg direction='in' type='s' />
    </method>
    <method name='ChangeBuffer'>
      <arg direction='in' type='s' />
    </method>
    <method name='SaveBuffer'>
      <arg direction='in' type='s' />
    </method>
    <method name='CloseBuffer'>
      <arg direction='in' type='s' />
    </method>
    <method name='Copy'>
      <arg direction='in' type='s' />
    </method>
    <method name='Cut'>
      <arg direction='in' type='s' />
    </method>
    <method name='Paste'>
      <arg direction='in' type='s' />
    </method>
    <method name='Undo'>
    </method>
    <method name='Revert'>
      <arg direction='in' type='s' />
    </method>
    <method name='FrameSetup'>
      <arg direction='in' type='b' />
    </method>
    <method name='SetDirectory'>
      <arg direction='in' type='s' />
    </method>
    <method name='GotoLine'>
      <arg name='1' direction='in' type='s' />
      <arg name='2' direction='in' type='i' />
    </method>
    <method name='StopEmacs'>
    </method>
  </interface>
</node>")

(defun register-dbus ()
  "register the dbus methods -- called at startup"
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "OpenFile"
   'pida-open-file)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "ChangeBuffer"
   'pida-change-buffer)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "CloseBuffer"
   'pida-kill-buffer)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "Copy"
   'pida-copy)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "SaveBuffer"
   'pida-save-buffer)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "Cut"
   'pida-cut)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "Paste"
   'pida-paste)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "Undo"
   'pida-undo)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "SetDirectory"
   'pida-set-dir)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "StopEmacs"
   'pida-stop-cb)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "FrameSetup"
   'pida-frame-setup)
  (dbus-register-method 
   :session
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   "uk.co.pida.Emacs"
   "GotoLine"
   'pida-goto-line)
  (dbus-register-method
   :session 
   emacs-dbus-ns
   "/uk/co/pida/Emacs"
   dbus-interface-introspectable 
   "Introspect" 
   'pida-emacs-introspect))

(setq inhibit-splash-screen 1)

;;; pida_emacs_dbus.el ends here
