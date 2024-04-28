  import { Component, OnInit } from '@angular/core';
  import { FormBuilder, FormGroup, Validators } from '@angular/forms';
  import { Router } from '@angular/router';
  import { AlertController, LoadingController } from '@ionic/angular';
  import { AuthenticationService } from 'src/app/core/services/authentication.service';

  @Component({
    selector: 'app-login',
    templateUrl: './login.page.html',
    styleUrls: ['./login.page.scss'],
  })
  export class LoginPage implements OnInit {
    credentials!: FormGroup;
    showPassword = false;

    constructor(
      private fb: FormBuilder,
      private authService: AuthenticationService,
      private alertController: AlertController,
      private router: Router,
      private loadingController: LoadingController
    ) {}

    ngOnInit() {
      this.credentials = this.fb.group({
        email: ['algorise@spn.com', [Validators.required, Validators.email]],
        password: ['ALGORISE', [Validators.required, Validators.minLength(6)]],
      });
    }

    async login() {
      const loading = await this.loadingController.create();
      await loading.present();
      this.authService.loginStatic(this.credentials.value).subscribe({
        next: async (res) => {
          await loading.dismiss();
          // Vérifiez si la connexion a réussi ou non
          if (res.success) {
            // Redirigez vers la page d'accueil ou toute autre page appropriée après la connexion réussie
            this.router.navigateByUrl('/intro', { replaceUrl: true });
          } else {
            // Affichez un message d'erreur si la connexion a échoué
            const alert = await this.alertController.create({
              header: 'Erreur de connexion',
              message: res.message,
              buttons: ['OK'],
            });
            await alert.present();
          }
        },
        error: async (err) => {
          await loading.dismiss();
          // Affichez un message d'erreur si une erreur survient pendant la connexion
          const alert = await this.alertController.create({
            header: 'Erreur de connexion',
            message: err,
            buttons: ['OK'],
          });
          await alert.present();
        },
      });
    }
    

    // Getter for easy access to form fields
    get email() {
      return this.credentials.get('email');
    }

    get password() {
      return this.credentials.get('password');
    }

    // Method to navigate to the register page
    navigateToSignUp() {
      this.router.navigate(['/signup']);
    }
  }
